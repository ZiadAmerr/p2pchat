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
from p2pchat.protocols.tcp_request_transceiver import TCPRequestTransceiver,UDPRequestTransceiver
from p2pchat.protocols.suap import SUAP_Request
from p2pchat.protocols.s4p import *
from p2pchat.utils.colors import *
from p2pchat.utils.chat_histoty import *
from p2pchat import data
import logging
#logging.basicConfig(level=logging.DEBUG)
import time
from p2pchat.custom_logger import app_logger #may use different loggers later
from p2pchat.globals import *
from p2pchat.utils.utils import validate_request
from tabulate import tabulate
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



class ClientUDPThread(threading.Thread):
    pass
class ClientTCPThread():
    """
    Responsible for establishing connections, sending the request,then recieving the response.
    for now, its a nonpersistent connection, single request/response cycle?
    
    """
    #TODO: change the name or make it a real thread
    def __init__(self, server_address, server_port):
        self.server_address = server_address
        self.server_port=server_port
        self.transceiver=TCPRequestTransceiver(None)
        self.client_auth=ClientAuth() #instance
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
    
    def login(self,username,password,tcp_port,udp_port):
        if not(self.connect()):
            return {"header":"","body":{"is_success":False,"message":"Connection failed"}}
        self.transceiver.send_message(SUAP_Request.logn_request(username,password,tcp_port,udp_port))
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
    
    def get_online_peers(self):

        if not(self.connect()):
            return {"header":"","body":{"is_success":False,"message":"Connection failed"}}
        self.transceiver.send_message({"type":"GTOP","username":self.client_auth.user['username']})
        response=self.transceiver.recieve_message()
        self.client_socket.close()
        return response      
    
    def create_chatroom(self,chatroom_key):

        if not(self.connect()):
            return {"header":"","body":{"is_success":False,"message":"Connection failed"}}
        self.transceiver.send_message({"type":"CRTM","user":self.client_auth.user,"chatroom_key":chatroom_key})
        response=self.transceiver.recieve_message()
        self.client_socket.close()
        return response      

    def get_chatrooms(self):
        if not(self.connect()):
            return {"header":"","body":{"is_success":False,"message":"Connection failed"}}
        self.transceiver.send_message({"type":"LISTRM","user":self.client_auth.user})
        response=self.transceiver.recieve_message()
        self.client_socket.close()
        return response      

    def get_chatroom(self,chatroom_key):
        if not(self.connect()):
            return {"header":"","body":{"is_success":False,"message":"Connection failed"}}
        self.transceiver.send_message(S4P_Request.gtrm_request(self.client_auth.user,chatroom_key))
        response=self.transceiver.recieve_message()
        self.client_socket.close()
        return response
        
        
    def admit_user_to_chatroom(self,user,chatroom_key):
   
        if not(self.connect()):
            return {"header":"","body":{"is_success":False,"message":"Connection failed"}}
        self.transceiver.send_message({"type":"ADMTUSR","caller":self.client_auth.user,"user":user,"chatroom_key":chatroom_key})
        response=self.transceiver.recieve_message()
        self.client_socket.close()
        return response

def requires_signin(func):
        def wrapper(self, *args, **kwargs):
            if getattr(self, 'user', None) is not None:  
                return func(self, *args, **kwargs)
            else:
                print(red_text(f"Operation Reqires user to be logged in,{self.to_dict()}"))
                return {"header":"","body":{"is_success":False,"message":"User not logged in"}}
        return wrapper
class ClientAuth:
    """client to server requests..."""
    #TODO: you have single client in the app, so you can use singleton for easier access
    #OPTIMIZATION: converted to singleton to utilize global access

    _clientAuth=None
    def __new__(cls):
        if not cls._clientAuth:
            cls._clientAuth = super().__new__(cls)
            cls._clientAuth._initialized = False
        return cls._clientAuth
    
    def __init__(self):
        if not self._initialized:
            self._initialized=True
            self.user=None
            self.available_rooms=[] #all chatrooms, updated by a thread
            self.current_chatroom=None
            self.current_chatroom_peers=None
            self.client_tcp_thread =ClientTCPThread('127.0.0.1', data.port_tcp)
            self.keep_alive_thread = KeepAliveThread('127.0.0.1',data.port_udp,user=self.user)
    
    def login(self,username:str,password:str,tcp_port:int,udp_port=None)->dict:
        """
        takes username and password, sends a login request to the server, and returns the response
        if request is successful, keep alive thread is started, user is returnred in client.user object.
        response dictionary is returnred as well
        """
        response=self.client_tcp_thread.login(username,password,tcp_port,udp_port)
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
            print(red_text("User not logged in"))
            return {"header":"","body":{"is_success":False,"message":"User not logged in"}}
        
        response=self.client_tcp_thread.get_online_peers()
        if response.get("body",{}).get("is_success"):
            return response.get("body",{}).get("data",{}).get("users",[])
        else:
            print(f"Failed to find peers: {response.get('body',{}).get('message')}")
            return []

    @requires_signin
    def create_chatroom(self,chatroom_key):
        response=self.client_tcp_thread.create_chatroom(chatroom_key)
        if response.get("body",{}).get("is_success"):
            print(green_text("Chatroom created successfully"))
        else:
            print(red_text(f"Chat room creation failed. {response.get('body',{}).get('message')}"))
            return None

    @requires_signin
    def get_chatrooms(self)->list:   
        response=self.client_tcp_thread.get_chatrooms()
        
        if response.get("body",{}).get("is_success"):
            self.available_rooms=response.get("body",{}).get("data",{}).get("rooms",[])
    
        return self.available_rooms


    @requires_signin
    def admit_user_to_chatroom(self,user,chatroom_key):
        """called by room owner to admit a user to a chatroom"""
        return self.client_tcp_thread.admit_user_to_chatroom(user,chatroom_key)


    @requires_signin
    def get_chatroom(self,chatroom_key) ->None |list:
        #get most recent chatroom members info 
        return  self.client_tcp_thread.get_chatroom(chatroom_key)
                
    @requires_signin
    def update_room_local_table(self,user):
        history.clear_volatile_messages()
        for i,member in enumerate(self.current_chatroom_peers):
            if member.get('username')==user.get('username'):
                self.current_chatroom_peers[i]=self.update_chatroom_entry(member,user)
                return
        #user is new, update local table 
        self.current_chatroom_peers=self._get_chatroom_table(self.current_chatroom)
        
    @requires_signin
    def _get_chatroom_table(self,chatroom_key):
        response=self.get_chatroom(chatroom_key)
        other_members=[]
        if response.get("body",{}).get("is_success"):
            chatroom_members=response.get("body",{}).get("data",{}).get("members",[]) # array of user dicts
            other_members=[member for member in chatroom_members if member.get("username")!=self.user.get("username")]
        else:
            print(red_text(f"Chat room entry failed. {response.get('body',{}).get('message')}"))
            return None
        return other_members
         
    def update_chatroom_entry(self,entry,user):
        for i in ['IP','PORT','PORT_UDP','is_active']:
            entry[i]=user[i]
        return entry
class PeerClient():
    """connect to other client to send requests
    will probably change to static"""
    def __init__(self):
        self.peer_socket=None
        self.transceiver=TCPRequestTransceiver(self.peer_socket)
        self.client_auth_instance= ClientAuth()
    def enter_chat(self,me,recepient):
        """
        return chat room key if successful, else 
        """
        if not(self.connect(recepient)):
            print(red_text("could not connect to user"))
            return  None
        self.transceiver.send_message(S4P_Request.privrm_request(self.client_auth_instance.user,recepient))
        response=self.transceiver.recieve_message()
        return PeerClient.process_response(response)
    
    

    def chat(self,me,recipient,chat_key):
        """
        will handle all messaging related stuff
        """
        #user started chatting, used to pause the cli loop
        #TODO: remove self.client_auth_instance.user, use client_auth_instance.user instead
        try:
            me_prompt_text="you >> "
            not_chatting.clear()
            peer_left.clear()
            is_in_chat.set()
            print_and_remember(green_text(f"Chat started with {recipient.get('username')}"),magenta_text("write exit_ to exit"))
            while not not_chatting.is_set(): #I know...
                if not ignore_input.is_set():
                    if not(self.connect(recipient)):
                        #won't work if outside the loop
                        print(red_text("could not connect to user"))
                        return  None
                    message=input(me_prompt_text)
                    if ignore_input.is_set():
                        continue
                    #if chat endded ignore the input
                    if peer_left.is_set():
                        not_chatting.set()
                        break
                    self.transceiver.send_message(S4P_Request.sndmsg_smpl_request(message,chat_key,self.client_auth_instance.user,recipient))
                    if message=='exit_':
                        is_in_chat.clear()
                        history.reset_history()
                        print(green_text(f"You left the conversation."))
                        break
                    print_and_remember(green_text(f"{self.client_auth_instance.user['username']} >> ")+message)
        finally:
            not_chatting.set()
            peer_left.set()
            print(magenta_text(f"Chat ended with {recipient.get('username')}  Press enter to continue."))

    def _refresh_uses_table(self):
        print_and_remember('?')
        while not not_chatting.is_set():
            active_usersnames=[green_text(i.get('username') )for i in self.client_auth_instance.current_chatroom_peers if i.get("is_active")]
            offline_usersnames=[red_text(i.get('username')) for i in self.client_auth_instance.current_chatroom_peers if not i.get("is_active")]
            print_in_constant_place(tabulate([[', '.join(active_usersnames),', '.join(offline_usersnames)]],headers=["ACTIVE USERS","OFFLINE USERS"],tablefmt="pretty"),key="peers status",ending_line='you >> ')
            time.sleep(5)

    def chatroom_chat(self):
        """
        will handle all messaging related stuff
        
        args

        chatroom: array of dicts of room JOIN members
        """
        #user started chatting, used to pause the cli loop
        print_and_remember(magenta_text(f"Chatroom started."))
        refresh_table=threading.Thread(target=self._refresh_uses_table)
        
        udp_transceiver=UDPRequestTransceiver()

        try:
            self.client_auth_instance.current_chatroom=self.client_auth_instance.current_chatroom
            me_prompt_text="you >> "
            not_chatting.clear()
            peer_left.clear()
            is_in_chat.set()
            refresh_table.start()
            popped_in_message=blue_text(f"{self.client_auth_instance.user['username']} just popped in !")
            for member in self.client_auth_instance.current_chatroom_peers:
                udp_transceiver.send_message(S4P_Request.sndmsg_smpl_request(popped_in_message,self.client_auth_instance.current_chatroom,self.client_auth_instance.user),(member.get('IP'),member.get('PORT_UDP')))

            print_and_remember(green_text(f"Chatroom started"),magenta_text("write exit_ to exit"))
            while not not_chatting.is_set(): #I know...
                if not ignore_input.is_set():
                    
                    message=input(me_prompt_text)
                    if ignore_input.is_set():
                        continue
                    #if chat endded ignore the input
                    if peer_left.is_set():
                        not_chatting.set()
                        break
                    for member in self.client_auth_instance.current_chatroom_peers:
                        udp_transceiver.send_message(S4P_Request.sndmsg_smpl_request(message,self.client_auth_instance.current_chatroom,self.client_auth_instance.user),(member.get('IP'),member.get('PORT_UDP')))

                    if message=='exit_':
                        is_in_chat.clear()
                        print(green_text(f"You left the conversation."))
                        break
                    print_and_remember(green_text(f"{self.client_auth_instance.user['username']} >> ")+message)
        finally:
            not_chatting.set()
            peer_left.set()
            self.client_auth_instance.current_chatroom=None
            self.client_auth_instance.current_chatroom_peers=None
            print(magenta_text(f"Chat ended with room {self.client_auth_instance.current_chatroom}  Press enter to continue."))

    def enter_chatroom(self,chatroom_key):
        if (self.client_auth_instance.current_chatroom):
            print(red_text(f"you are already in a chatroom {self.client_auth_instance.current_chatroom}"))
            return
        other_members=self.client_auth_instance._get_chatroom_table(chatroom_key)
        if other_members is None:
            print(red_text(f"could not enter chatroom, make sure you are a member first"))
            return
        self.client_auth_instance.current_chatroom=chatroom_key
        self.client_auth_instance.current_chatroom_peers=other_members
        self.chatroom_chat()

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
    
    def join_chatroom(self,chatroom:dict):
        """
        sends a join chatroom request to the owner, and returns the response in {header:"",body:{}} format
        chatroom: chat room entry dict {_id,key,owner,IP,PORT}, where IP and PORT are the owner's ip and port
        """
        if not validate_request(chatroom,["key","owner","IP","PORT"]):
            print(red_text(f"invalid chatroom entry, {chatroom}"))
            return None
        if not(self.connect(chatroom)):
            print(red_text("could not connect to owner"))
            return  None
        
        self.transceiver.send_message(S4P_Request.joinrm_request(ClientAuth().user,chatroom.get("key")))
        response=self.transceiver.recieve_message()
        return PeerClient.process_response(response)


    @staticmethod
    def process_response(response):
        if not response:
            print(red_text('empty response'))
            return None
        message=response.get("body",{}).get("message",None)
        if not response or not response.get("body",{}).get("is_success"):
            print(red_text(message if message else "request succeeeded"))
        else:
            print(green_text(message if message else "request failed"))
        return response

