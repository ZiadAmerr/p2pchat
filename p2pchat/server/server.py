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
from p2pchat.utils.utils import sigint_handler
from p2pchat.protocols.suap import SUAP_Response
import logging
class ServerUDPThread(threading.Thread):
    def __init__(self, address, port):
        super().__init__()
        self.address = address
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.bind((self.address, self.port))
        self.shutdown_flag = threading.Event()


    def run(self):
        logging.info(f'UDP server thread started at port {self.port}')
        while not self.shutdown_flag.is_set():
            try:
                request, addr = self.server_socket.recvfrom(1024) #only use for HELLO CALLS
                request=pickle.loads(request)
                # Process received request
                # For example, print received message
                print(f"Received message from {addr}: {request}")
                if not validate_request(request.get("body"),["type","username"]):
                    return print("invalid request")
                DB.set_last_seen(request.get("body").get("username"))
            except Exception as e:
                print("Exception Occued: ",traceback.print_exc(e))
                return None


    def stop(self):
        self.shutdown_flag.set()
        self.server_socket.close()

class ServerTCPThread(threading.Thread):
    """
    a thread thats responsible for auth (for now)
    """
    def __init__(self, address, port):
        super().__init__()
        self.address = address
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.address, self.port))
        self.shutdown_flag = threading.Event()

    def handle_auth_request(client_socket,socket_address):
        #consider using pooling or other non resource-intensive method
        #TODO: create an internal Server Error response and handler
        try:
            authentication_manager=AuthenticationManager(socket_address)
            transceiver=TCPRequestTransceiver(client_socket)
            request=transceiver.recieve_message()
            if request is None:
                #cleanup
                client_socket.close()
                del authentication_manager
                del transceiver
                return None
            logging.info(str(request))
            response=authentication_manager.handle_request(request)
            transceiver.send_message(response.to_dict())
        except Exception as e:
            import traceback 
            traceback.print_exc()
            transceiver.send_message(SUAP_Response.ENTRNL(e).to_dict())
    def run(self):
        logging.info(f'TCP server thread started at port {self.port}')
        self.server_socket.listen(1000)
        while not self.shutdown_flag.is_set():
            try:
                client_socket,address=self.server_socket.accept()
                logging.info(f'connection from {address} has been established')
                client_handler=threading.Thread(target=ServerTCPThread.handle_auth_request,args=(client_socket,address))
                client_handler.start()
            except Exception as e:
                print("Exception Occued: ",traceback.print_exc(e))
                return None


    def stop(self):
        self.shutdown_flag.set()
        self.server_socket.close()
# Example usage
import signal
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    signal.signal(signal.SIGINT, sigint_handler)

    server_udp_thread = ServerUDPThread('127.0.0.1', data.port_udp)
    server_tcp_thread =ServerTCPThread('127.0.0.1',data.port_tcp)
    server_tcp_thread.start()
    server_udp_thread.start()

    # Perform other operations or run the client here

    # When done, stop the server thread
    # server_thread.stop()  # Call this when you want to stop the server
