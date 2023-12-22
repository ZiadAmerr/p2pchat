import re
import time


def welcome_state():
    print("Welcome to Our chat")
    print()

    has_account = input("Do you have an account? (y/n): ")

    if has_account == "y":
        return "Login"
    elif has_account == "n":
        return "Sign Up"


def login_state():
    if "incorrect_attempt" in state_data and state_data["incorrect_attempt"] >= 3:
        print("Account locked. Try again in 1 minute.")
        return None

    if "incorrect_attempt" in state_data and state_data["incorrect_attempt"]:
        print("Incorrect username or password")
        print()

    username = input("Username: ")
    password = input("Password: ")

    if len(password) < 6:
        print("Invalid password. Password must be at least 6 digits long.")
        return "Login"

    if (username == "hanna" and password == "123456") or (
        username == "ziad" and password == "456789"
    ):
        state_data["incorrect_attempt"] = 0
        return "Main Menu"
    else:
        state_data["incorrect_attempt"] = state_data.get("incorrect_attempt", 0) + 1
        return "Login"


def signup_state():
    email = input("Email: ")
    username = input("Username: ")
    password = input("Password: ")

    if not re.match(r"^\w+@\w+\.\w+$", email):
        print("Invalid email address.")
        return "Sign Up"

    if username in usernames:
        print("Username already exists.")
        return "Sign Up"

    if len(password) < 6:
        print("Invalid password. Password must be at least 6 digits long.")
        return "Sign Up"

    usernames.add(username)
    state_data["users"][email] = {"username": username, "password": password}
    return "Main Menu"


def menu_state():
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
    elif choice == "3":
        return "send msg"
    elif choice == "4":
        return "join"
    elif choice == "5":
        return "list"
    elif choice == "6":
        return "exit"


"""def show_your_profile_state():
    print("Your Profile")
    print("Username:", state_data["user"]["username"])
    print("ID:", state_data["user"]["id"])

    if state_data["user"]["chat_history"]:
        print("Chat History:")
        for message in state_data["user"]["chat_history"]:
            print(f"{message['timestamp']}: {message['message']}")
    else:
        print("No chat history found.")

    print()
    print("1. Back to Main Menu")

    choice = input("Please enter your choice: ")
    if choice == "1":
       next_state = "Main Menu"
    else:
      print("Invalid choice. Please try again.")
    next_state = "Show Your Profile" """


def send_msg_state():
    recipient_username = input("Enter the username of the recipient: ")
    if recipient_username not in usernames:
        print("User with username", recipient_username, "not found.")
    else:
        message = input("Enter your message: ")
        print("Message sent successfully!")

    return "Main Menu"


def join_room_state():
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
        user_input = (
            input("Use SEND to send a message or EXIT to leave the room: ")
            .strip()
            .upper()
        )

        if user_input.startswith("SEND"):
            choice = input("Enter your message:")
            print(f"Your message has been sent.")

        elif user_input == "EXIT":
            print(f"You have left the '{joined_room}' room.")
            break
        else:
            print("Invalid input. Please try again.")

    return "Main Menu"


def list_state():
    online_users = ["hanna", "ziad", "gira"]
    print("Online Users:")
    if online_users:
        for user in online_users:
            print(f"{user}")
    else:
        print("No users are currently online.")

    return "Main Menu"


def exit_state():
    return "Welcome"


chat_history = []
state_data = {
    "incorrect_attempt": 0,
    "users": {
        "hanna": {"username": "hanna", "password": "123456", "id": "112233"},
        "ziad": {"username": "ziad", "password": "456789", "id": "332211"},
    },
}
state_data["user"] = {}
usernames = set(state_data["users"].keys())
state_data["user"]["chat_history"] = chat_history


def main():
    state = "Welcome"

    while True:
        choice = None
        if state == "Welcome":
            next_state = welcome_state()
        elif state == "Login":
            next_state = login_state()
        elif state == "Sign Up":
            next_state = signup_state()
        elif state == "Main Menu":
            next_state = menu_state()
            ##if next_state == "show your profile":
            ## next_state = show_your_profile_state()
            if next_state == "send msg":
                next_state = send_msg_state()
            elif next_state == "join":
                next_state = join_room_state()
            elif next_state == "list":
                next_state = list_state()
            elif next_state == "exit":
                next_state = exit_state()

        elif next_state is None:
            # time.sleep(60)
            # state_data["incorrect_attempt"] = 0
            # next_state = "Login"
            exit()

        state = next_state


if __name__ == "__main__":
    main()
