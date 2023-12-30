import threading

#global threads to share bettween server and client threads
peer_left=threading.Event()
not_chatting=threading.Event()
is_in_chat=threading.Event()
ignore_input=threading.Event()

not_chatting.set()
peer_left.clear()
is_in_chat.clear()
ignore_input.clear()
"""
peer_left:      when server detects peer is left, it sets this event,
                so that we can ignore next input from this client and go to main ment (buffer to ignore input)

not_chatting:   used by the main loop to continue or pause

is_in_chat  :   used to reject reqeusts if already in private chat

ignore_input:   used whenever you wish your current request to inturrpt others. for example, if u are chatting and somone wished to join the room,
                you can set this event in the server thread, and check it in chatting thread to ignore the input
"""
