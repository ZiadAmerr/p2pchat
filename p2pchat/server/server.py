import __init__
import threading
import traceback
import socket
import pickle
import select
import logging
import sys
from time import sleep
from typing import List, Union, Dict
from psutil import process_iter
from signal import SIGTERM

from p2pchat.server.monitor import UsersMonitor
from p2pchat.protocols.tcp_request_transceiver import TCPRequestTransceiver
from p2pchat.protocols.suap import SUAP_Response
from p2pchat.utils.utils import validate_request
from p2pchat.utils.colors import colorize
from p2pchat.data import port_tcp, port_udp
from p2pchat.server.server_db import myDB as DB
from p2pchat.server.authentication_manager import AuthenticationManager


class SockerManager:
    def __init__(self, address, port):
        self.address = address
        self.port = port
        self.socket = None

    def start_socket(self):
        raise NotImplementedError

    def handle_request(self):
        raise NotImplementedError

    def deactivate(self):
        raise NotImplementedError


class UDPManager(SockerManager):
    def start_socket(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.bind((self.address, self.port))
        logging.info(f"UDP server thread started at port {self.port}")

    def handle_request(self):
        """
        may convert to factory to handle different requests in future
        """
        request, addr = self.server_socket.recvfrom(1024)
        request = pickle.loads(request)

        logging.debug(f"Received message from {addr}: {request}")
        if not validate_request(request.get("body"), ["type"]):
            return logging.warn("invalid request")
        try:
            DB.set_last_seen(request.get("body").get("username"))
        except Exception as e:
            logging.error(
                f"error while setting last seen for {request.get('body').get('username')}: {e}"
            )
            return None

    def deactivate(self):
        self.server_socket.close()
        logging.info(f"UDP server thread stopped at port {self.port}")


class TCPManager(SockerManager):
    """
    a thread thats responsible for auth (for now)
    """

    def start_socket(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.server_socket.bind((self.address, self.port))
        except OSError:
            for proc in process_iter():
                for conns in proc.connections(kind="inet"):
                    if conns.laddr.port == self.port:
                        proc.send_signal(SIGTERM)
            sleep(3)
            try:
                self.server_socket.bind((self.address, self.port))
            except OSError:
                logging.error(
                    f"TCP server thread failed to start at port {self.port} due to OSError"
                )
                return None

        self.server_socket.listen(1000)
        logging.info(f"TCP server thread started at port {self.port}")

    def handle_auth_request(client_socket, socket_address):
        # consider using pooling or other non resource-intensive method
        # TODO: create an internal Server Error response and handler
        try:
            authentication_manager = AuthenticationManager(socket_address)
            transceiver = TCPRequestTransceiver(client_socket)
            request = transceiver.recieve_message()
            response = authentication_manager.handle_request(request)
            transceiver.send_message(response.to_dict())
            client_socket.close()
        except Exception as e:
            import traceback

            traceback.print_exc()
            transceiver.send_message(SUAP_Response.ENTRNL(e).to_dict())
        finally:
            client_socket.close()
            del authentication_manager
            del transceiver
            return None

    def handle_request(self):
        try:
            client_socket, address = self.server_socket.accept()
            logging.info(f"connection from {address} has been established")
            client_handler = threading.Thread(
                target=TCPManager.handle_auth_request, args=(client_socket, address)
            )
            client_handler.start()
        except Exception as e:
            print("Exception Occued: ", traceback.print_exc(e))
            return None

    def deactivate(self):
        self.server_socket.close()
        logging.info(f"TCP server thread stopped at port {self.port}")


def terminate(
    clients_montior: UsersMonitor,
    sockets_managers: List[Union[TCPManager, UDPManager]],
    recurse_limit=4,
):
    if recurse_limit < 0:
        return

    try:
        clients_montior.deactivate()
        for manager in sockets_managers:
            manager.deactivate()
        sys.exit(0)
    except KeyboardInterrupt:
        terminate(recurse_limit=recurse_limit - 1)


if __name__ == "__main__":
    server_udp_manager = UDPManager("127.0.0.1", port_udp)
    server_tcp_manager = TCPManager("127.0.0.1", port_tcp)
    clients_montior = UsersMonitor()
    clients_montior.start()

    sockets_managers: List[Union[TCPManager, UDPManager]] = [
        server_tcp_manager,
        server_udp_manager,
    ]

    managers_socks = {}
    for manager in sockets_managers:
        manager.start_socket()
        managers_socks[manager] = manager.server_socket

    socket_to_manager: Dict[socket.socket, Union[TCPManager, UDPManager]] = {
        v: k for k, v in managers_socks.items()
    }

    socks = list(managers_socks.values())

    try:
        while socks:
            readable, _, _ = select.select(socks, [], [])
            for s in readable:
                socket_to_manager[s].handle_request()
    except KeyboardInterrupt:
        print(colorize("KeyboardInterrupt - terminating...", "red"))
        terminate(clients_montior, sockets_managers)
