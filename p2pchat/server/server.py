"""
The server should have a tcp and udp threads,
tcp should handle sign in,sign up,login, get peers (next phase message queues) requests,
udp should handle HELLO messages, it recieves username in message data, and uses DB.set_last_seen to activate the user (set his last seen to now)
the server must have a thread that checks every minute the last seen of all users, and if it is more than 3 minutes, it should deactivate the user

udp thread:
    while true:
    recieve message
    if message is HELLO:
        DB.set_last_seen(message.data) #asynchronous
    else:
        ignore

tcp thread:
    while true:
    recieve message
    if message is auth_related:
        prepare auth_manager:
        if message is SIGNUP:
            auth_manager.signup(message.data)
        elif message is LOGIN:
            auth_manager.login(message.data)
        elif message is GET_PEERS:
            DB.get_online()
        else
            err
    else:
        ignore for now
"""
import __init__
import threading
import traceback
import socket
import pickle
from p2pchat.utils.utils import validate_request
from p2pchat.server.server_db import myDB as DB
from p2pchat.server.authentication_manager import AuthenticationManager
from p2pchat.protocols.tcp_request_transceiver import TCPRequestTransceiver
from p2pchat import data
from p2pchat.protocols.suap import SUAP_Response
from p2pchat.custom_logger import logging
import select
import logging
from p2pchat.server.monitor import UsersMonitor


class SockerManager():
    def __init__(self, address, port):
        self.address = address
        self.port = port
        self.server_socket=None
    def start_socket(self):
        raise NotImplementedError
    def handle_request(self):
        raise NotImplementedError
class UDPManager(SockerManager):
    
        
    def start_socket(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.bind((self.address, self.port))
        logging.info(f'UDP server thread started at port {self.port}')

    def handle_request(self):
        """
        may convert to factory to handle different requests in future
        """
        request, addr = self.server_socket.recvfrom(1024)
        request=pickle.loads(request)

        logging.debug(f"Received message from {addr}: {request}")
        if not validate_request(request.get("body"),["type","username"]):
            return logging.warn("invalid request")
        try:
            DB.set_last_seen(request.get("body").get("username"))
        except Exception as e:
            logging.error(f"error while setting last seen for {request.get('body').get('username')}: {e}")
            return None
    
class TCPManager(SockerManager):
    """
    a thread thats responsible for auth (for now)
    """
    def start_socket(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.address, self.port))
        self.server_socket.listen(1000)
        logging.info(f'TCP server thread started at port {self.port}')

    def handle_auth_request(client_socket,socket_address):
        #consider using pooling or other non resource-intensive method
        #TODO: create an internal Server Error response and handler
        try:
            authentication_manager=AuthenticationManager(socket_address)
            transceiver=TCPRequestTransceiver(client_socket)
            request=transceiver.recieve_message()
            response=authentication_manager.handle_request(request)
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
            client_socket,address=self.server_socket.accept()
            logging.info(f'connection from {address} has been established')
            client_handler=threading.Thread(target=TCPManager.handle_auth_request,args=(client_socket,address))
            client_handler.start()
        except Exception as e:
            print("Exception Occued: ",traceback.print_exc(e))
            return None


if __name__ == "__main__":
    
    server_udp_manager= UDPManager('127.0.0.1', data.port_udp)
    server_tcp_manager= TCPManager('127.0.0.1',data.port_tcp)
    clients_montior=UsersMonitor()
    clients_montior.start()
    sockets_managers=[server_tcp_manager,server_udp_manager]
    managers_socks={}
    for manager in sockets_managers:
        manager.start_socket()
        managers_socks[manager]=manager.server_socket
    socket_to_manager={v:k for k,v in managers_socks.items()}
    
    socks=list(managers_socks.values())
    while socks:
        readable,_,_=select.select(socks,[],[])
        for s in readable:
            socket_to_manager[s].handle_request()
