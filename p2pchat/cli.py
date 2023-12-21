import __init__
from p2pchat.peer.peer_client import Client
import re
import time
import uuid  # Import the UUID module
from p2pchat.custom_logger import app_logger
import logging
logging.basicConfig(level=logging.DEBUG)
class App:
    def __init__(self):
        self.client=Client()
        self.incorrect_attempt = {"incorrect_attempt": 0}
    
    def welcome_state(self):
        print("Welcome to Our chat")
        print()
        has_account = input("Do you have an account? (y/n): ")

        while has_account not in ['y','n']:
            print("Please enter a valid response")
            has_account = input("Do you have an account? (y/n): ")
        if has_account == "y":
            return "Login"
        elif has_account == "n":
            return "Sign Up"


    def login_state(self):
        if "incorrect_attempt" in self.incorrect_attempt and self.incorrect_attempt["incorrect_attempt"] >= 3:
            print("Account locked. Try again in 1 minute.")
            return None

        if "incorrect_attempt" in self.incorrect_attempt and self.incorrect_attempt["incorrect_attempt"]:
            print("Incorrect username or password")
            print()

        username = input("Username: ")
        password = input("Password: ")

        if len(password) < 6:
            print("Invalid password. Password must be at least 6 digits long.")
            return "Login"
        
        response=self.client.login(username, password)
        app_logger.debug(response)
        if response.get("body").get("is_success") == True:
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

        if len(password) < 6:
            print("Invalid password. Password must be at least 6 digits long.")
            return "Sign Up"
        response=self.client.signup(username,password)
        app_logger.debug(response)
        if response.get("body").get("is_success") == False:
            print(response.get("body").get("message"))
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
        if recipient_username not in usernames:
            print("User with username", recipient_username, "not found.")
        else:
            message = input("Enter your message: ")
            print("Message sent successfully!")
        
            if "communicated_with" not in self.state_data['user']:
                self.state_data['user']['communicated_with'] = set()

            self.state_data['user']['communicated_with'].add(recipient_username)

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
        online_users = ["hanna", "ziad", "gira"]  
        print("Online Users:")
        if online_users:
            for user in online_users:
                print(f"{user}")
        else:
            print("No users are currently online.")

        return "Main Menu"

    def exit_state(self):
        self.client.logout()
        print("Goodbye!")
        return "Welcome"





    def main(self):
        state = "Welcome"
        while True:
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
                app_logger.debug("next_state is None")
                time.sleep(60)
                self.incorrect_attempt["incorrect_attempt"] = 0
                next_state = "Login"

            state = next_state


if __name__ == "__main__":
    my_app= App()
    my_app.main()