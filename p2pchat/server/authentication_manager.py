import __init__
from p2pchat.protocols.suap import SUAP_Response
from p2pchat.server.request_handler import *
from p2pchat.server.server_db import myDB as DB
from p2pchat.utils import utils


class AuthenticationManager:

    """
    Handles the authentication-related requests from the clients.
    1-registration
    2-login
    3-logout
    to handle many requests at the same time, treading will be used along with this class
    handle_request(request) -> SUAP_Response

    this class is not responsible for sending the response to the client,
    it only handles the request and returns the SAUP_Response,
    the server (or another class) will interact with this class to get the response,
    then and send it to the client


    requset: dict in the form of {header:<headerinfo>,data:{type:<request_type>,username:<username>,...}}
    connection_address: atuple of (host,port), can be aquired from the socket, check server_playground
    future note: we might move the request type to the header
    """

    types = {"RGST", "LOGN", "LGDN", "CLRS","GTOP","CRTM","LISTRM","ADMTUSR","GTRM"}

    def __init__(self, connection_address):
        self.connection_address = connection_address
        self.type = None

    def handle_request(self, request) -> SUAP_Response:
        """
        parses the recieved request and handle it accordingly
        """
        if not request.get("body", {}).get("type") or request.get("body", {}).get("type") not in self.types:
            raise Exception("handle_request: Invalid Request")
        request_handler = handler_factory(
            request.get("body").get("type")
        )
        return request_handler.handle_request(self.connection_address, request)


    


if __name__ == "__main__":
    AM = AuthenticationManager(("localhost", 8000))
    print(
        AM.handle_request(
            {
                "header": "",
                "data": {"type": "RGST", "username": "user", "password": "pass"},
            }
        )
    )
    print(
        AM.handle_request(
            {
                "header": "",
                "data": {"type": "LOGN", "username": "user", "password": "pass"},
            }
        )
    )
    print(
        AM.handle_request({"header": "", "data": {"type": "LGDN", "username": "user"}})
    )
    print(
        AM.handle_request({"header": "", "data": {"type": "CLRS", "username": "user"}})
    )
