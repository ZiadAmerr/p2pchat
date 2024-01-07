import __init__
import time

from p2pchat.utils.utils import clear_console


def print_and_remember(*args, ending_line=None):
    text = " ".join([str(arg) for arg in args])
    history.append(text)
    clear_console()
    history.print_chat(ending_line)


def print_in_constant_place(*args, key=None, ending_line=None):
    text = " ".join([str(arg) for arg in args])
    if key is None:
        print_and_remember(
            "key must be provided to constant messages", ending_line=ending_line
        )
    new_history = []
    found = False
    for message in history.history:
        if not (
            isinstance(message, tuple)
            and len(message) == 3
            and message[1:3] == ("constant", key)
        ):
            new_history.append(message)
        else:
            new_history.append((text, "constant", key))
            found = True
    if not found:
        new_history.append((text, "constant", key))

    if history.history != new_history:
        history.history = new_history
        clear_console()
        history.print_chat(ending_line)


def print_volatile_message(*args, ending_line=None):
    text = " ".join([str(arg) for arg in args])
    history.append((text, "volatile"))
    history.print_chat(ending_line)


class History:
    def __init__(self):
        self.history = []

    def append(self, msg):
        self.history.append(msg)

    def reset_history(self):
        self.history = []

    def print_chat(self, ending_line=None):
        clear_console()
        for msg in self.history:
            print(msg if isinstance(msg, str) else msg[0])
        if ending_line:
            print(ending_line, end="")

    def clear_volatile_messages(self):
        self.history = [
            msg for msg in self.history if isinstance(msg, str) or msg[1] != "volatile"
        ]
        self.print_chat()


history = History()

if __name__ == "__main__":
    print_and_remember("hello", "world")
    time.sleep(1)
    print_in_constant_place("room members", key="room_members")
    time.sleep(1)
    print_and_remember("hello", "world")
    time.sleep(1)
    print_and_remember("hello", "world")
    time.sleep(1)
    print_in_constant_place("room memberschanged", key="room_members")
    time.sleep(1)
