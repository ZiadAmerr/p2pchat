import traceback
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
import socket
import pickle
from p2pchat.protocols.tcp_request_transceiver import TCPRequestTransceiver
from p2pchat.protocols.suap import SUAP_Request
from p2pchat import data
import logging
import time

class KeepAliveThread(threading.Thread):
    """
    thread classs for the HELLO PULSE request, it sends a HELLO (LGDN) message every 20 seconds to the server 
    ---if peer is signed in---
    """
    def __init__(self, server_address, server_port,interval=20,user=None):
        super().__init__()
        self.server_address = server_address
        self.server_port = server_port
        self.interval=interval
        self.user=user
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.shutdown_flag = threading.Event()


    def run(self):
        logging.info(f'UDP client thread started')
        while not self.shutdown_flag.is_set():
            try:
                if self.user:
                    message=pickle.dumps(
                        {"header":"",
                         "body":SUAP_Request.is_logged_in_request(self.user.get("username"),"whatever")}
                        )

                    self.client_socket.sendto(message,(self.server_address,self.server_port)) 
                time.sleep(self.interval)
            except Exception as e:
                print("Exception Occued: ",traceback.print_exc(e))
                return None


    def stop(self):
        self.shutdown_flag.set()
        self.server_socket.close()

class ClientTCPThread():
    """
    Responsible for establishing connections, sending the request,then recieving the response.
    """
    def __init__(self, server_address, server_port):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_address = server_address
        self.server_port=server_port
        self.transceiver=TCPRequestTransceiver(self.client_socket)
    def connect(self):
        try:
            self.client_socket.connect((self.server_address, self.server_port))            
        except ConnectionRefusedError:
            print("Connection refused. Server may not be available.")
        except TimeoutError:
            print("Connection attempt timed out.")
        except OSError as e:
            print("socket is already connected:", e)
        except Exception as e:
            print("An error occurred during connection:", e)

    def login(self,username,password):
        self.connect()
        self.transceiver.send_message(SUAP_Request.logn_request(username,password))
        response=self.transceiver.recieve_message()
        return response
    
    def signup(self,username,password):
        self.connect()
        self.transceiver.send_message(SUAP_Request.rgst_request(username,password))
        response=self.transceiver.recieve_message()
        return response
        
# Example usage

class Client:
    def __init__(self):
        self.user=None
        self.client_tcp_thread =ClientTCPThread('127.0.0.1', data.port_tcp)
        self.keep_alive_thread = KeepAliveThread('127.0.0.1',data.port_udp,user=self.user)
    def login(self,username,password):
        response=self.client_tcp_thread.login(username,password)
        if response.get("body",{}).get("is_success"):
            self.user=response.get("body").get("data")    
            self.keep_alive_thread.user=self.user
        else:
            print(f"Failed to login: {response.get('body').get('message')}",response)
    def signup(self,username,password):
        response=self.client_tcp_thread.signup(username,password)
        print (response)
        
if __name__=="__main__":
    logging.basicConfig(level=logging.INFO)
    client=Client()
    client.login("test","test")
    print(client.user)
    if(client.user):
        
        client.keep_alive_thread.start()
