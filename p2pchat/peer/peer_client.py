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
from p2pchat.protocols.s4p import *
from p2pchat.utils.colors import *
from p2pchat.utils.chat_histoty import *
from p2pchat import data
import logging
#logging.basicConfig(level=logging.DEBUG)
import time
from p2pchat.custom_logger import app_logger #may use different loggers later
from p2pchat.globals import not_chatting,peer_left,is_in_chat
class KeepAliveThread(threading.Thread):
    """
    thread classs for the HELLO PULSE request, it sends a HELLO (LGDN) message every 20 seconds to the server 
    ---if peer is signed in---
    """
    def __init__(self, server_address, server_port,interval=4,user=None):
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

class ClientTCPThread():
    """
    Responsible for establishing connections, sending the request,then recieving the response.
    for not, its a nonpersistent connection, single request/response cycle
    """
    #TODO: change the name or make it a real thread
    def __init__(self, server_address, server_port):
        self.server_address = server_address
        self.server_port=server_port
        self.transceiver=TCPRequestTransceiver(None)
    
    def connect(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.server_address, self.server_port))     
            self.transceiver.connection=self.client_socket
            return True
        except ConnectionRefusedError:
            app_logger.warning("Connection refused. Server may not be available.")
        except TimeoutError:
            app_logger.warning("Connection attempt timed out.")
        except OSError as e:
            app_logger.error("socket is already connected:", e)
            return True
        except Exception as e:
            app_logger.error("An error occurred during connection:", e)
        return False
    
    def login(self,username,password,tcp_port):
        if not(self.connect()):
            return {"header":"","body":{"is_success":False,"message":"Connection failed"}}
        self.transceiver.send_message(SUAP_Request.logn_request(username,password,tcp_port))
        response=self.transceiver.recieve_message()
        self.client_socket.close()
        return response
    
    def signup(self,username,password):
        if not(self.connect()):
            return {"header":"","body":{"is_success":False,"message":"Connection failed"}}
        self.transceiver.send_message(SUAP_Request.rgst_request(username,password))
        response=self.transceiver.recieve_message()
        self.client_socket.close()
        return response
   
    def logout(self,username):
        if not(self.connect()):
            return {"header":"","body":{"is_success":False,"message":"Connection failed"}}
        self.transceiver.send_message(SUAP_Request.clear_session_request(username,'whatever'))
        response=self.transceiver.recieve_message()
        self.client_socket.close()
        return response
    
    def get_online_peers(self,username):

        if not(self.connect()):
            return {"header":"","body":{"is_success":False,"message":"Connection failed"}}
        self.transceiver.send_message({"type":"GTOP","username":username})
        response=self.transceiver.recieve_message()
        self.client_socket.close()
        return response      


class ClientAuth:
    def __init__(self):
        self.user=None
        self.client_tcp_thread =ClientTCPThread('127.0.0.1', data.port_tcp)
        self.keep_alive_thread = KeepAliveThread('127.0.0.1',data.port_udp,user=self.user)

    def login(self,username:str,password:str,tcp_port:int,udp_port=None)->dict:
        """
        takes username and password, sends a login request to the server, and returns the response
        if request is successful, keep alive thread is started, user is returnred in client.user object.
        response dictionary is returnred as well
        """
        response=self.client_tcp_thread.login(username,password,tcp_port)
        if response.get("body",{}).get("is_success"):
            self.user=response.get("body").get("data")
            self.keep_alive_thread.user=self.user
            self.keep_alive_thread.start()
        else:
            print(f"Failed to login: {response.get('body',{}).get('message')}")
        return response
        
    def signup(self,username:str,password:str)->dict:
        """
        takes username and password, sends a signup request to the server, and returns the response in {header:"",body:{}} format
        """
        return self.client_tcp_thread.signup(username,password)
    
    def logout(self):
        """
        sends a logout request to the server, and returns the response in {header:"",body:{}} format
        """
        self.client_tcp_thread.logout(self.user.get("username"))
        self.keep_alive_thread.stop()
        self.user=None
    
    def get_online_peers(self):
        """
        sends a get online peers request to the server, and returns the response in {header:"",body:{}} format
        """

        if not self.user:
            print("User not logged in")
            return {"header":"","body":{"is_success":False,"message":"User not logged in"}}
        
        response=self.client_tcp_thread.get_online_peers(self.user.get("username"))
        if response.get("body",{}).get("is_success"):
            return response.get("body",{}).get("data",{}).get("users",[])
        else:
            print(f"Failed to find peers: {response.get('body',{}).get('message')}")
            return []

class PeerClient():
    """will probably change to static"""
    def __init__(self):
        self.peer_socket=None
        self.transceiver=TCPRequestTransceiver(self.peer_socket)
    def enter_chat(self,me,recepient):
        """
        return chat room key if successful, else 
        """
        if not(self.connect(recepient)):
            print(red_text("could not connect to user"))
            return  None
        self.transceiver.send_message(S4P_Request.privrm_request(me,recepient))
        response=self.transceiver.recieve_message()
        if response and response.get("body",{}).get("is_success"):
            return response
        else:
            print('user refused to chat with you')
            return None
    
    def chat(self,me,recipient,chat_key):
        """
        will handle all messaging related stuff
        """
        #user started chatting, used to pause the cli loop
        
        try:
            me_prompt_text="you >> "
            not_chatting.clear()
            peer_left.clear()
            is_in_chat.set()
            print_and_remember(green_text(f"Chat started with {recipient.get('username')}"),magenta_text("write exit_ to exit"))
            while True and not not_chatting.is_set(): #I know...
                if not(self.connect(recipient)):
                    #won't work if outside the loop
                    print(red_text("could not connect to user"))
                    return  None
                message=input(me_prompt_text)
                #if chat endded ignore the input
                if peer_left.is_set():
                    not_chatting.set()
                    break
                self.transceiver.send_message(S4P_Request.sndmsg_smpl_request(message,chat_key,me,recipient))
                if message=='exit_':
                    is_in_chat.clear()
                    print(green_text(f"You left the conversation."))
                    break
                print_and_remember(green_text(f"{me['username']} >> ")+message)
        finally:
            not_chatting.set()
            peer_left.set()
            print(magenta_text(f"Chat ended with {recipient.get('username')}  Press enter to continue."))
            
        
    
    def connect(self,user):
        try:
            #before connecting to someone, make sure to close any previous connection
            self.disconnect()
            self.peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.peer_socket.connect((user["IP"], user["PORT"]))     
            self.transceiver.connection=self.peer_socket
            return True
        except ConnectionRefusedError:
            logging.warning(f"Connection refused. Server at {user['IP']}:{user['PORT']} may not be available.")
        except TimeoutError:
            logging.warning("Connection attempt timed out.")
        except OSError as e:
            logging.error("socket is already connected:", e)
            return True
        except Exception as e:
            logging.error("An error occurred during connection:", e)
        return True
    
    def disconnect(self):
        try:
            self.peer_socket.close()
            self.peer_socket=None
        except Exception as e:
            logging.debug(f"An error occurred during disconnection: {e}")
            pass
    
    


if __name__=="__main__":
    logging.basicConfig(level=logging.INFO)
    client=Client()
    client.signup("test5","test5")
    client.login("test5","test5")
