import p2pchat.data as data
import pickle

class RequestTransceiver:
    """
    this is intended to be a class that wraps the socket.recv/socket.send functions
    it will be used to:
    1-send and recieve requests/responses to/from  the server
    
    *** the messages will be in the form of a dictionary (can be actually any picklable object but naah)***
    usage:
    send_message(message:dict)->None
    recieve_message()->dict or None
    """
    def __init__(self,connection):
        self.connection=connection
        self.type=None
        self.message=None
        self.header_size=data.header_size
        self.packet_size=max(20,self.header_size)
        self.full_message=None
        self.new_message=True
        self.message_length=None

    def _gather_message(self,dest=None,message=None):
        if message is None:
            return dest
        if dest is None:
            dest=message
        else :
            dest+=message
        return dest

    def recieve_message(self)->dict:
        while True:
            message = self.connection.recv(self.packet_size)
            if(self.new_message and message):
                self.message_length=int(message[:self.header_size])
                self.new_message=False
            self.full_message=self._gather_message(self.full_message,message)
            print(len(self.full_message),self.message_length)
            if len(self.full_message)-self.header_size==self.message_length:
                self.message=pickle.loads(self.full_message[self.header_size:])
                break
        self.full_message=None
        self.new_message=True
        return self.message

    def send_message(self,message:dict):
        message_in_bytes=pickle.dumps(message)
        self.connection.send(self._add_header(message_in_bytes))

    def _add_header(self,message:bytes)->bytes:
        """
        adds any necessary information to the message header, for example, message size
        need to address what headers are important and how they are formatted, otherwise we will need to add more bytes for a config-file-like headers
        """
        message_size=f'{len(message):<{self.header_size}}'
        return bytes(message_size,'utf-8')+message