import p2pchat.data as data
import pickle
import logging


class TCPRequestTransceiver:
    """
    this is intended to be a class that wraps the socket.recv/socket.send TCP functions
    it will be used to:
    1-send and recieve requests/responses to/from  the server

    *** the messages will be in the form of a dictionary (can be actually any picklable object but naah)***
    usage:
    send_message(message:dict)->None
    recieve_message()->dict or None
    """

    header_size = data.header_size
    packet_size = max(20, header_size)

    def __init__(self, connection):
        self.connection = connection
        self.type = None
        self.message = None
        self.full_message = None
        self.new_message = True
        self.message_length = None

    def _gather_message(self, dest=None, message=None):
        if message is None:
            return dest
        if dest is None:
            dest = message
        else:
            dest += message
        return dest

    def recieve_message(self) -> dict:
        # TODO: add a timeout
        try:
            if self.new_message:
                header = self.connection.recv(self.header_size)
                if not len(header):
                    return None
                self.message_length = int(header)
                self.new_message = False
            while True:
                self.full_message = self._gather_message(
                    self.full_message, self.connection.recv(self.packet_size)
                )
                if len(self.full_message) > self.message_length:
                    logging.WARN("hmmm, check this out")
                if len(self.full_message) == self.message_length:
                    self.message = pickle.loads(self.full_message)
                    break
            self.full_message = None
            self.new_message = True
            return {"header": header, "body": self.message}
        except Exception as e:
            print("Connection broken: ", e)
            return None

    def send_message(self, message: dict):
        message_in_bytes = pickle.dumps(message)
        self.connection.send(self._add_header(message_in_bytes))

    @staticmethod
    def _add_header(message: bytes) -> bytes:
        # TODO: move to utils or common class
        """
        adds any necessary information to the message header, for example, message size
        need to address what headers are important and how they are formatted, otherwise we will need to add more bytes for a config-file-like headers
        """
        message_size = f"{len(message):<{TCPRequestTransceiver.header_size}}"
        return bytes(message_size, "utf-8") + message
