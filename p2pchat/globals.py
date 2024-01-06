import threading

# global threads to share bettween server and client threads
peer_left = threading.Event()
not_chatting = threading.Event()
is_in_chat = threading.Event()
ignore_input = threading.Event()

not_chatting.set()
peer_left.clear()
is_in_chat.clear()
ignore_input.clear()
