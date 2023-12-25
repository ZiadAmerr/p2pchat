import __init__
from p2pchat.peer.peer_client import *
from p2pchat.peer.peer_server import *

import time
import uuid  # Import the UUID module
from p2pchat.custom_logger import app_logger
import logging
from p2pchat.utils.colors import *
from p2pchat.utils.utils import clear_console
from p2pchat.utils.chat_histoty import history,print_and_remember
from p2pchat.globals import not_chatting
logging.basicConfig(level=logging.INFO)

class App:
    def __init__(self):
        self.client_auth=ClientAuth()
        self.incorrect_attempt = {"incorrect_attempt": 0}
        self.active_peers=[]
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
        print("1. Show your profile")
        print("2. Show others' profiles")
        print("3. Send a private message")
        print("4. Join Available Rooms")
        print("5. List online users")
        print("6. Exit")
        

        choice = input("Please enter your choice: ")
        if choice == "1":
            return "show your profile"
        elif choice =="2":
            return "show others' profile"
        elif choice =="3":
            return "send msg"
        elif choice == "4":
            return "join"
        elif choice =="5":
            return "list"
        elif choice =="6":
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
    #YAGNI
    def show_others_profile_state(self):
        print("Show Others' Profile")

        profile_username = input("Enter the username of the profile you want to view: ")
        if profile_username in usernames:
            print(f"Profile of {profile_username}:")
            print(f"Username: {self.state_data['users'][profile_username]['username']}")
            print(f"ID: {self.state_data['users'][profile_username]['id']}")
        else:
            print(f"User with username {profile_username} not found.")



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
        available_rooms = ["General", "Sports", " politics"]

        print("Available Rooms:")
        for i, room_name in enumerate(available_rooms, start=1):
            print(f"{i}. {room_name}")

        choice = int(input("Enter the number of the room you want to join: "))

        try:
            if not 1 <= choice <= len(available_rooms):
                print("Invalid room number. Please try again.")
                return "Main Menu"
        except ValueError:
            print("Invalid input. Please enter a number.")
            return "Main Menu"
        
        joined_room = available_rooms[choice - 1]
        print(f"You have successfully joined the '{joined_room}' room.")

        while True: 
            user_input = input("Use SEND to send a message or EXIT to leave the room: ").strip().upper()

            if user_input.startswith("SEND"):
                choice = input("Enter your message:")
                print(f"Your message has been sent.")

            elif user_input == "EXIT":
                print(f"You have left the '{joined_room}' room.")
                break
            else:
                print("Invalid input. Please try again.")

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
            if state == "Welcome":
                next_state = self.welcome_state()
            elif state == "Login":
                next_state = self.login_state()
            elif state == "Sign Up":
                next_state = self.signup_state()
            elif state == "Main Menu":
                next_state= self.menu_state()
                if next_state == "show your profile":
                    next_state = self.show_your_profile_state()
                elif next_state == "show others' profile":
                    next_state = self.show_others_profile_state()
                elif next_state == "send msg":
                    next_state= self.send_msg_state()
                elif next_state =="join":
                    next_state= self.join_room_state()
                elif next_state =="list":
                    next_state= self.list_state()
                elif next_state =="exit":
                    next_state= self.exit_state()
            elif next_state is None:
                if self.client_auth.user is not None:
                    next_state="Main Menu"
                else:
                    time.sleep(60)
                    self.incorrect_attempt["incorrect_attempt"] = 0
                    next_state = "Login"

            state = next_state


if __name__ == "__main__":
    my_app= App()
    my_app.main()
    
    