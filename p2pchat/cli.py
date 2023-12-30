import __init__
from p2pchat.peer.peer_client import *
from p2pchat.peer.peer_server import *
from tabulate import tabulate
import time
import uuid  # Import the UUID module
from p2pchat.custom_logger import app_logger
import logging
from p2pchat.utils.colors import *
from p2pchat.utils.utils import clear_console
from p2pchat.utils.chat_histoty import history,print_and_remember
from p2pchat.globals import not_chatting,ignore_input
logging.basicConfig(level=logging.INFO)

class App:
    def __init__(self):
        self.client_auth=ClientAuth()
        self.incorrect_attempt = {"incorrect_attempt": 0}
        self.active_peers=[]
        self.client_auth.available_rooms=[]
        self.peer_server=PeerServer()
        self.peer_client=PeerClient()

    def welcome_state(self):
        print("Welcome to Our chat")
        print()
        has_account = input("Do you have an account? (y/n): ")

        while has_account not in ['y','n']:
            print(yellow_text("Please enter a valid response"))
            has_account = input("Do you have an account? (y/n): ")
        if has_account == "y":
            return "Login"
        elif has_account == "n":
            return "Sign Up"

    def login_state(self):
        if self.client_auth.user is not None:
            return "Main Menu"
        
        if "incorrect_attempt" in self.incorrect_attempt and self.incorrect_attempt["incorrect_attempt"] >= 3:
            print(red_text("Account locked. Try again in 1 minute."))
            return None

        if "incorrect_attempt" in self.incorrect_attempt and self.incorrect_attempt["incorrect_attempt"]:
            print(red_text("Incorrect username or password"))
            print()

        username = input("Username: ")
        password = input("Password: ")

        """ if len(password) < 6:
            print(red_text("Invalid password. Password must be at least 6 digits long."))
            return "Login"
         """
        response=self.client_auth.login(username, password, self.peer_server.tcp_manager.port,self.peer_server.udp_manager.port)
        if response.get("body",{}).get("is_success"):
            self.peer_server.start()
            self.peer_server.set_user(self.client_auth.user)
            self.incorrect_attempt["incorrect_attempt"] = 0
            return "Main Menu"
        else:
            self.incorrect_attempt["incorrect_attempt"] = self.incorrect_attempt.get("incorrect_attempt", 0) + 1
            return "Login"

    def signup_state(self):
        #email = input("Email: ")
        username = input("Username: ")
        password = input("Password: ")
    
        """ if not re.match(r"^\w+@\w+\.\w+$", email):
            print("Invalid email address.")
            return "Sign Up" """

        """ if len(password) < 6:
            print("Invalid password. Password must be at least 6 digits long.")
            return "Sign Up" """
        response=self.client_auth.signup(username,password)
        app_logger.debug(response)
        if response.get("body",{}).get("is_success") == False:
            print(response.get("body",{}).get("message"))
            return "Sign Up"
        

        print("Account created successfully!")

        return "Welcome"

    def menu_state(self):
        print("Main Menu")
        print("1. Create room")
        print("2. List available rooms")
        print("3. Enter chatroom")
        print("4. Join Room")
        print("5. List online users")
        print("6. Send a private message")
        print("7. Exit")
        

        choice = input("Please enter your choice: ")
        if choice == "1":
            return "create room"
        elif choice =="2":
            return "list rooms"
        elif choice =="3":
            return "Enter chatroom"
        elif choice == "4":
            return "Join Room"
        elif choice =="5":
            return "list users"
        elif choice =="6":
            return "Send a private message"
        elif choice =="7":
            return "exit"
        else:
            return "Main Menu"
        
    def show_your_profile_state(self):
        print("Your Profile")

        if "username" in self.state_data["user"]:
            print(f"Username: {self.state_data['user']['username']}")
            print(f"ID: {self.state_data['user']['id']}")

            communicated_with = self.state_data['user'].get('communicated_with', set())

            if communicated_with:
                print("Users You've Chat With:")
                for user in communicated_with:
                    print(user)
            else:
                print("No chat history yet.")
        else:
            print("Username not found.")
            if self.state_data["users"]:
                print("Generating your profile...")
                username = self.state_data["users"]["email"]["username"]  
                user_id = str(uuid.uuid4())  # Generate a random UUID for ID

                self.state_data["user"]["username"] = username
                self.state_data["user"]["id"] = user_id

                print("Your Profile:")
                print(f"Username: {self.state_data['user']['username']}")
                print(f"ID: {self.state_data['user']['id']}")
            else:
                print("Please sign up to create your profile.")

        return "Main Menu"
    
    def create_chatroom_state(self):
        print("Create a chatroom")
        room_name = input("Enter the name of the chatroom: ")
        res=self.client_auth.create_chatroom(room_name)

        return "Main Menu"
    
    def list_rooms_state(self):
        print("List available rooms")
        self.client_auth.available_rooms = self.client_auth.get_chatrooms()
        if len(self.client_auth.available_rooms):
            headers=[bold_text(i) for i in["ROOM KEY","OWNER","OWNER STATUS"]]
            data=[]
            for room in self.client_auth.available_rooms:
                status= yellow_text('you') if room['owner']==self.client_auth.user['username'] else green_text('Available') if room['is_active'] else red_text('Not Available') #iknow...
                data.append ([room['key'],room['owner'],status])
            print(tabulate(data,headers=headers,tablefmt="pretty"))
        else:
            print("No rooms available.")
       
        return "Main Menu"

    def send_msg_state(self):
        recipient_username = input("Enter the username of the recipient: ")
        if recipient_username not in [user["username"] for user in self.active_peers] :
            self.active_peers=self.client_auth.get_online_peers()
            if recipient_username not in [user["username"] for user in self.active_peers] :
                print("User with username", recipient_username, "is either offline or not found.")
                return "Main Menu"
        user=next(user for user in self.active_peers if user["username"]==recipient_username)
        self.recipient=user
        history.reset_history()
        response=self.peer_client.enter_chat(self.client_auth.user,user)
        if response and response.get('body').get('code') ==52 : #shof tare2a a7san
            key=response.get('body').get('data').get('key')
            
            self.peer_server.setup_chat(key)
            print_and_remember(blue_text("you are the client"))
            self.peer_client.chat(self.client_auth.user,user,key)
            self.peer_server.end_chat()
        else:
            print(red_text("couldn't connect"))
        return "Main Menu"

    def join_room_state(self):
        print ("Join a room")
        chat_room=input("Enter Chatroom key: ")

        if chat_room not in [room["key"] for room in self.client_auth.available_rooms] :
            self.client_auth.available_rooms=self.client_auth.get_chatrooms()

        if chat_room not in [room["key"] for room in self.client_auth.available_rooms] :
            print("Room with key doesn't exist")
            return "Main Menu"

        room=next(room for room in self.client_auth.available_rooms if room["key"]==chat_room)
        if not room['is_active']:
            print(red_text("Room owner is offline"))
            return "Main Menu"
        response=self.peer_client.join_chatroom(room)
        
        return "Main Menu"
   
    def enter_chatroom_state(self):
        print("Enter a chatroom")
        chatroom_key = input("Enter the name of the chatroom: ")
        if chatroom_key not in [room["key"] for room in self.client_auth.available_rooms] :
            self.client_auth.get_chatrooms()

        if chatroom_key not in [room["key"] for room in self.client_auth.available_rooms] :
            print(red_text("Chatroom not found."))
            return "Main Menu"
        
        self.peer_client.enter_chatroom(chatroom_key)
        return "Main Menu"

    def list_state(self):
        
        online_users = self.client_auth.get_online_peers()
        print("Online Users:")
        if len(online_users):
            self.active_peers=online_users
            for user in online_users:
                print(f"- {user['username']}")
        else:
            print("No users are currently online.")
        print()
        return "Main Menu"

    def exit_state(self):
        self.client_auth.logout()
        print("Goodbye!")
        return "Welcome"



    def main(self):
        state = "Welcome"
        while True:
            not_chatting.wait()
            if (ignore_input.is_set()):
                time.sleep(1)
                continue
            if state == "Welcome":
                next_state = self.welcome_state()
            elif state == "Login":
                next_state = self.login_state()
            elif state == "Sign Up":
                next_state = self.signup_state()
            elif state == "Main Menu":
                next_state= self.menu_state()
                if next_state == "create room":
                    next_state = self.create_chatroom_state()
                elif next_state == "list rooms":
                    next_state = self.list_rooms_state()
                elif next_state == "send msg":
                    next_state= self.send_msg_state()
                elif next_state =="Join Room":
                    next_state= self.join_room_state()
                elif next_state =="list users":
                    next_state= self.list_state()
                elif next_state =="exit":
                    next_state= self.exit_state()
                elif next_state =="Enter chatroom":
                    next_state= self.enter_chatroom_state()
            elif next_state is None:
                if self.client_auth.user is not None:
                    next_state="Main Menu"
                else:
                    time.sleep(60)
                    self.incorrect_attempt["incorrect_attempt"] = 0
                    next_state = "Login"

            state = next_state


if __name__ == "__main__":
    while True:
        my_app= App()
        my_app.main()
    