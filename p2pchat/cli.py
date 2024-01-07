import __init__
from tabulate import tabulate
from time import sleep
import uuid
import logging
from pwinput import pwinput

from p2pchat.custom_logger import app_logger
from p2pchat.peer.peer_client import PeerClient, ClientAuth
from p2pchat.peer.peer_server import PeerServer
from p2pchat.utils.colors import colorize
from p2pchat.utils.chat_history import history, print_and_remember, clear_console
from p2pchat.globals import not_chatting, ignore_input

# logging.basicConfig(level=logging.INFO)

IDLE_WAIT = 1  # change to 3 for slower changing between screens


MAIN_MENU_TEXT = f"""
{colorize(f'{colorize("Welcome to Our chat", "magenta")} - {colorize("Main Menu", "yellow")}', 'underline')}

Choices:
    {colorize('1', 'green')}. Create room
    {colorize('2', 'green')}. List available rooms
    {colorize('3', 'green')}. Enter chatroom
    {colorize('4', 'green')}. Join Room
    {colorize('5', 'green')}. List online users
    {colorize('6', 'green')}. Send a private message
    {colorize('7', 'red')}. Logout
"""


def show_profile(username, id, communicated_with):
    print(f"Username: {username}")
    print(f"ID: {id}")

    communicated_with = communicated_with

    if communicated_with:
        print("Users You've Chat With:")
        for user in communicated_with:
            print(user)
    else:
        print("No chat history yet.")


def print_menu(choice):
    if choice == "chatroom_menu":
        print(
            f"""
{colorize('Create a chatroom', 'yellow')}

{colorize('Enter chatroom name to create: ', 'green')}""",
            end="",
        )


class App:
    def __init__(self):
        self.client_auth = ClientAuth()
        self.incorrect_attempt = {"incorrect_attempt": 0}
        self.active_peers = []
        self.client_auth.available_rooms = []
        self.peer_server = PeerServer()
        self.peer_client = PeerClient()

    def welcome_state(self):
        clear_console()
        print(colorize(colorize("Welcome to Our chat", "underline"), "magenta"))
        print()
        has_account = input(
            f"Do you have an account? ({colorize('y', 'green')}/{colorize('n', 'red')}): "
        )

        while has_account not in ["y", "n"]:
            clear_console()
            print(
                colorize("Please enter a valid response, as", "yellow"),
                colorize(f"{has_account}", "red"),
                colorize("is not a valid response", "yellow"),
            )
            has_account = input("Do you have an account? (y/n): ")

        if has_account in ["y", "n"]:
            return {"y": "Login", "n": "Sign Up"}[has_account]

    def login_state(self):
        if self.client_auth.user is not None:
            return "Main Menu"

        if (
            "incorrect_attempt" in self.incorrect_attempt
            and self.incorrect_attempt["incorrect_attempt"] >= 3
        ):
            print(colorize("Account locked. Try again in 1 minute.", "red"))
            return None

        if (
            "incorrect_attempt" in self.incorrect_attempt
            and self.incorrect_attempt["incorrect_attempt"]
        ):
            print(colorize("Incorrect username or password", "red"))
            print()

        if self.incorrect_attempt["incorrect_attempt"] > 0:
            print(
                colorize("Type ", "magenta")
                + colorize("!exit", "red")
                + colorize(" if you want to go back to the previous menu", "magenta")
            )
        username = input("Username: ")

        if username == "!exit":
            return "Welcome"

        password = pwinput("Password: ")

        response = self.client_auth.login(
            username,
            password,
            self.peer_server.tcp_manager.port,
            self.peer_server.udp_manager.port,
        )
        if response.get("body", {}).get("is_success"):
            self.peer_server.start()
            self.peer_server.set_user(self.client_auth.user)
            self.incorrect_attempt["incorrect_attempt"] = 0

            print(colorize(f"Welcome {username}!", "green"))

            return "Main Menu"
        else:
            self.incorrect_attempt["incorrect_attempt"] = (
                self.incorrect_attempt.get("incorrect_attempt", 0) + 1
            )
            return "Login"

    def signup_state(self):
        print(colorize("Create an account!", "yellow"))

        print(
            colorize(
                "Type '!exit' if you want to go back to the previous menu", "magenta"
            )
        )
        username = input("Username: ")
        if username == "!exit":
            return "Welcome"
        password = pwinput("Password: ")

        """ if not re.match(r"^\w+@\w+\.\w+$", email):
            print("Invalid email address.")
            return "Sign Up" """

        """ if len(password) < 6:
            print("Invalid password. Password must be at least 6 digits long.")
            return "Sign Up" """
        response = self.client_auth.signup(username, password)
        app_logger.debug(response)
        if response.get("body", {}).get("is_success") == False:
            print(response.get("body", {}).get("message"))
            return "Sign Up"

        print(
            colorize(
                f"Account created successfully! You will be redirected in {IDLE_WAIT} seconds.",
                "green",
            )
        )

        return "Welcome"

    def menu_state(self):
        print(MAIN_MENU_TEXT)

        choice = input("Please enter your choice: ")
        if choice == "1":
            return "create room"
        elif choice == "2":
            return "list rooms"
        elif choice == "3":
            return "Enter chatroom"
        elif choice == "4":
            return "Join Room"
        elif choice == "5":
            return "list users"
        elif choice == "6":
            return "send msg"
        elif choice == "7":
            return "exit"
        else:
            return "Main Menu"

    def show_your_profile_state(self):
        print("Your Profile")

        if "username" in self.state_data["user"]:
            show_profile(
                self.state_data["user"]["username"],
                self.state_data["user"]["id"],
                self.state_data["user"].get("communicated_with", set()),
            )
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
        print_menu("chatroom_intro")
        room_name = input()
        self.client_auth.create_chatroom(room_name)
        return "Main Menu"

    def list_rooms_state(self):
        print("List available rooms")
        self.client_auth.available_rooms = self.client_auth.get_chatrooms()
        if len(self.client_auth.available_rooms):
            headers = [
                colorize(i, "bold") for i in ["ROOM KEY", "OWNER", "OWNER STATUS"]
            ]
            data = []
            for room in self.client_auth.available_rooms:
                status = (
                    colorize("you", "yellow")
                    if room["owner"] == self.client_auth.user["username"]
                    else colorize("Available", "green")
                    if room["is_active"]
                    else colorize("Not Available", "red")
                )  # iknow...
                data.append([room["key"], room["owner"], status])
            print(tabulate(data, headers=headers, tablefmt="pretty"))
        else:
            print("No rooms available.")

        return "Main Menu"

    def send_msg_state(self):
        recipient_username = input("Enter the username of the recipient: ")
        if recipient_username not in [user["username"] for user in self.active_peers]:
            self.active_peers = self.client_auth.get_online_peers()
            if recipient_username not in [
                user["username"] for user in self.active_peers
            ]:
                print(
                    "User with username",
                    recipient_username,
                    "is either offline or not found.",
                )
                return "Main Menu"
        user = next(
            user for user in self.active_peers if user["username"] == recipient_username
        )
        self.recipient = user
        history.reset_history()
        response = self.peer_client.enter_chat(self.client_auth.user, user)
        if response and response.get("body").get("code") == 52:  # shof tare2a a7san
            key = response.get("body").get("data").get("key")

            self.peer_server.setup_chat(key)
            print_and_remember(colorize("you are the client", "blue"))
            self.peer_client.chat(self.client_auth.user, user, key)
            self.peer_server.end_chat()
        else:
            print(colorize("couldn't connect", "red"))
        return "Main Menu"

    def join_room_state(self):
        print("Join a room")
        chat_room = input("Enter Chatroom key: ")

        if chat_room not in [room["key"] for room in self.client_auth.available_rooms]:
            self.client_auth.available_rooms = self.client_auth.get_chatrooms()

        if chat_room not in [room["key"] for room in self.client_auth.available_rooms]:
            print("Room with key doesn't exist")
            return "Main Menu"

        room = next(
            room
            for room in self.client_auth.available_rooms
            if room["key"] == chat_room
        )
        if not room["is_active"]:
            print(colorize("Room owner is offline", "red"))
            return "Main Menu"
        response = self.peer_client.join_chatroom(room)

        return "Main Menu"

    def enter_chatroom_state(self):
        print("Enter a chatroom")
        chatroom_key = input("Enter the name of the chatroom: ")
        if chatroom_key not in [
            room["key"] for room in self.client_auth.available_rooms
        ]:
            self.client_auth.get_chatrooms()

        if chatroom_key not in [
            room["key"] for room in self.client_auth.available_rooms
        ]:
            print(colorize("Chatroom not found.", "red"))
            return "Main Menu"

        self.peer_client.enter_chatroom(chatroom_key)
        return "Main Menu"

    def list_state(self):
        online_users = self.client_auth.get_online_peers()
        print("Online Users:")
        if len(online_users):
            self.active_peers = online_users
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
            if ignore_input.is_set():
                continue
            if state == "Welcome":
                next_state = self.welcome_state()
            elif state == "Login":
                next_state = self.login_state()
            elif state == "Sign Up":
                next_state = self.signup_state()
            elif state == "Main Menu":
                next_state = self.menu_state()
                if next_state == "create room":
                    next_state = self.create_chatroom_state()
                elif next_state == "list rooms":
                    next_state = self.list_rooms_state()
                elif next_state == "send msg":
                    next_state = self.send_msg_state()
                elif next_state == "Join Room":
                    next_state = self.join_room_state()
                elif next_state == "list users":
                    next_state = self.list_state()
                elif next_state == "exit":
                    next_state = self.exit_state()
                elif next_state == "Enter chatroom":
                    next_state = self.enter_chatroom_state()
            elif next_state is None:
                if self.client_auth.user is not None:
                    next_state = "Main Menu"
                else:
                    # sleep(2)
                    self.incorrect_attempt["incorrect_attempt"] = 0
                    next_state = "Login"

            sleep(IDLE_WAIT)
            clear_console()
            state = next_state


if __name__ == "__main__":
    while True:
        my_app = App()
        my_app.main()
