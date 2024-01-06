import socket, logging, select, threading, traceback
from p2pchat.server.server import SockerManager
from p2pchat.utils.colors import *
from p2pchat.utils import utils
from p2pchat.protocols.s4p import S4P_Response
from p2pchat.utils.chat_histoty import (
    history,
    print_and_remember,
    print_volatile_message,
)
from p2pchat.peer.peer_client import PeerClient
from p2pchat.globals import *
from p2pchat.peer.peer_client import *


class PeerTCPManager(SockerManager):
    """
    TODO: the notifications,, put is_in_chat to use.
    TODO: can we move setup and end_chat to more general class?
    """

    def __init__(self, address):
        self.address = address
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((address, 0))
        self.port = self.socket.getsockname()[1]
        self.chat_thread = None
        self.chat_key = None
        self.user = None

    def handle_request(self):
        try:
            peer_socket, address = self.socket.accept()
            transciver = TCPRequestTransceiver(peer_socket)
            request = transciver.recieve_message()
            if request:
                # print(red_text(f"{bold_text('incoming'),request.get('body',{})}"))
                if request.get("body", {}).get("type") == "PRIVRM":
                    res = self.handle_new_chat_request(request).to_dict()
                    if res.get("is_success"):
                        transciver.send_message(res)
                        client = PeerClient()
                        print_and_remember(blue_text("you are the server"))
                        self.chat_thread = threading.Thread(
                            target=client.chat,
                            args=(
                                self.user,
                                request.get("body").get("sender"),
                                self.chat_key,
                            ),
                        )
                        self.chat_thread.start()
                    else:
                        transciver.send_message(res)
                elif request.get("body", {}).get("type") == "SNDMSG":
                    res = self.handle_send_message_request(request).to_dict()
                    transciver.send_message(res)
                elif request.get("body", {}).get("type") == "JOINRM":
                    res = self.handle_join_room_request(request).to_dict()
                    transciver.send_message(res)

        except Exception as e:
            print("Exception Occued: ", e, traceback.print_exc())
            return None

    def handle_new_chat_request(self, request):
        sender = request.get("body").get("sender").get("username")
        if is_in_chat.is_set():
            print_volatile_message(blue_text(f"{sender} tried to contact you"))
            threading.Timer(5, history.clear_volatile_messages).start()
            return S4P_Response.RCPNTREF("Already in chat")
        if not utils.validate_request(request["body"], ["sender", "recipient"]):
            return S4P_Response.INCRAUTH(
                "Invalid Request, Enter chat must have username"
            )
        print(f"Incoming request? Press enter to continue")
        ignore_input.set()
        not_chatting.clear()
        a = input(f"{sender} wants to chat with you? (y/n): ")
        while a not in ["y", "n"]:
            print(red_text("invalid input"))
            a = input(f"{sender} wants to chat with you? (y/n): ")
        response = None
        if a == "y":
            is_in_chat.set()
            history.reset_history()
            key = utils.get_unique_id()
            self.chat_key = key
            response = S4P_Response.CREATDRM(f"your request was accepted", {"key": key})
        elif a == "n":
            not_chatting.set()
            response = S4P_Response.RCPNTREF(
                f"your private room request has been rejected "
            )
        ignore_input.clear()
        return response

    def handle_send_message_request(self, request):
        """handles reciving message requests"""
        if not is_in_chat.is_set():
            print(red_text("can't send while user not in chat"))
            return S4P_Response.UNKWNERR(f"can't send while user not in chat")

        if not request or request.get("body", {}).get("key") != self.chat_key:
            print(red_text("Invalid Request, no or invalid key"), request)
            return S4P_Response.INCRAUTH("Invalid Request, no or invalid key")

        sender = request.get("body", {}).get("sender").get("username", "unknown")
        message = request.get("body", {}).get("message", "")
        if message == "exit_":
            peer_left.set()
            self.end_chat()
            print(
                green_text(
                    f"{sender} left the conversation. Press enter to continue... "
                )
            )
            return S4P_Response.MESGSENT(f"message recieved ;)", None)
        print_and_remember(
            f"{yellow_text(f'{sender} >> ')} {message}", ending_line="you >> "
        )
        return S4P_Response.MESGSENT(f"message recieved", None)

    def start_socket(self):
        self.socket.listen(20)

    def setup_chat(self, chat_key):
        self.chat_key = chat_key
        is_in_chat.set()
        not_chatting.clear()
        peer_left.clear()

    def end_chat(self):
        self.chat_key = None
        is_in_chat.clear()

    def deactivate(self):
        self.socket.close()

    def handle_join_room_request(self, request):
        # if  is_in_chat.is_set():
        #    print(red_text("user is busy, try again later")) #store it for later?
        #    return S4P_Response.UNKWNERR(f"can't send while user not in chat")

        if not request or not utils.validate_request(
            request.get("body", {}), ["sender", "chatroom_key"]
        ):
            print(red_text("Invalid Request"), request)
            return S4P_Response.INCRAUTH("Invalid Request, no or invalid key")

        sender = request.get("body", {}).get("sender", {})
        chatroom_key = request.get("body", {}).get("chatroom_key")
        print_volatile_message(f"Incoming request? Press enter to continue")
        ignore_input.set()
        a = input(
            blue_text(f"{sender.get('username')} wants to join {chatroom_key}? (y/n): ")
        )
        while a not in ["y", "n"]:
            print_volatile_message(red_text("invalid input"))
            a = input(f"{sender.get('username')} wants to join {chatroom_key}? (y/n): ")
        res = None
        if a == "y":
            me_to_server_client = ClientAuth()
            response = me_to_server_client.admit_user_to_chatroom(sender, chatroom_key)
            if response.get("body").get("is_success"):
                print_volatile_message(
                    green_text(
                        f"{sender.get('username')} was added to chatroom \"{chatroom_key}\" successfully."
                    )
                )
                res = S4P_Response.JOINEDRM(
                    f"your request was accepted", {"key": chatroom_key}
                )
            else:
                print_volatile_message(red_text("couldn't admit user to chatroom."))
                res = S4P_Response.UNKWNERR(
                    f"Couldn't join chatroom, try again later, or may be you are already registerd"
                )
            time.sleep(2)
            history.clear_volatile_messages()
            print_and_remember("")
        else:
            res = S4P_Response.RCPNTREF(f"your private room request has been rejected ")
        ignore_input.clear()
        return res


class PeerUDPManager(SockerManager):
    def __init__(self, address):
        self.address = address
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.address, 0))
        self.port = self.socket.getsockname()[1]

    def handle_request(self):
        try:
            udp_transciver = UDPRequestTransceiver(self.socket)
            request, address = udp_transciver.recieve_message()
            if request:
                # print(red_text(f"{bold_text('incoming'),request.get('body',{})}"))
                if request.get("body", {}).get("type") == "SNDMSG":
                    res = self.handle_send_message_request(request).to_dict()
                    udp_transciver.send_message(res, address)

        except Exception as e:
            print("Exception Occued: ", e, traceback.print_exc())
            return None

    def handle_send_message_request(self, request):
        """handles reciving message requests"""
        if not is_in_chat.is_set():
            # print(red_text("can't send while user not in chat.?"))
            return S4P_Response.UNKWNERR(f"can't send while user not in chat")

        if (
            not request
            or request.get("body", {}).get("key") != ClientAuth().current_chatroom
        ):
            print(red_text("Invalid Request, no or invalid key"), request)
            return S4P_Response.INCRAUTH("Invalid Request, no or invalid key")

        sender_name = request.get("body", {}).get("sender").get("username", "unknown")
        ClientAuth().update_room_local_table(request.get("body", {}).get("sender"))

        message = request.get("body", {}).get("message", "")
        if message == "exit_":
            print_and_remember(magenta_text(f"{sender_name} left the conversation"))
            return S4P_Response.MESGSENT(f"message recieved ;)", None)
        print_and_remember(
            f"{yellow_text(f'{sender_name} >> ')} {message}", ending_line="you >> "
        )
        return S4P_Response.MESGSENT(f"message recieved", None)

    def start_socket(self):
        pass

    def deactivate(self):
        self.socket.close()


class PeerServer(threading.Thread):
    def __init__(self, address="127.0.0.1"):
        super().__init__()
        self.tcp_manager = PeerTCPManager(address)
        self.udp_manager = PeerUDPManager(address)
        self.peer_credentails = None
        logging.info(f"peer tcp port: {self.tcp_manager.port}")
        logging.info(f"peer udp port: {self.udp_manager.port}")
        self.work = False

    def set_user(self, user):
        self.tcp_manager.user = user
        self.udp_manager.user = user

    def setup_chat(self, chat_key):
        self.tcp_manager.setup_chat(chat_key)

    def end_chat(self):
        self.tcp_manager.end_chat()

    def _activate(self):
        self.tcp_manager.start_socket()
        self.udp_manager.start_socket()

    def _deactivate(self):
        self.tcp_manager.deactivate()
        self.udp_manager.deactivate()

    def run(self):
        print(f"started listening at :{self.tcp_manager.port}")
        self.work = True
        self._activate()
        socket_to_manager = {
            mngr.socket: mngr for mngr in [self.tcp_manager, self.udp_manager]
        }
        socks = list(socket_to_manager.keys())
        while socks and self.work:
            readable, _, _ = select.select(socks, [], [])
            for s in readable:
                threading.Thread(target=socket_to_manager[s].handle_request).start()

    def stop(self):
        self.work = False
        self._deactivate()
