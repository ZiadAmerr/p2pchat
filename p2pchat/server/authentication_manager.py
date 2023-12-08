import bcrypt
import sys
print(sys.path)
from p2pchat.protocols.suap import SUAP_Response
from p2pchat.server.server_db import ServerDB as DB

class AuthenticationManager:
    """
    Handles the authentication-related requests from the clients
    #will be modified to take full request instead of custom inputs, as it will need ip for most requests.    
    handle_request(request) -> SUAP_Response
    """
    types = {"RGST", "LOGN", "LGDN", "CLRS"}

    def __init__(self, connection):
        self.connection = connection
        self.type = None
        
    def handle_request(self,request)->SUAP_Response:
        """
        parses the recieved request and handle it accordingly
        """
        raise NotImplementedError

    def _handle_rgst_request(self, username: str, password: str) -> SUAP_Response:
        f"""Creates a new user account with the provided username and password.

        Returns
        -------
        SUAP_Response
            Returns a SUAP_Response with codes:
                {SUAP_Response.render_code("NEWREG")}
                {SUAP_Response.render_code("CNFLCT")}
        """
        self.type = "RGST"

        # Check if account with such username already exists
        if DB.account_exists(username):
            DB.register_user(username, bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()))
            return SUAP_Response.NEWREG(f"Account {username} created successfully")
        else:
            return SUAP_Response.CNFLCT("Username already exists")


    def _handle_rgst_request(self, username: str, password: str) -> SUAP_Response:
        f"""Logs in a user using username and password

        Returns
        -------
        SUAP_Response
            Returns a SUAP_Response with codes:
                {SUAP_Response.render_code("NEWLOG")}
                {SUAP_Response.render_code("OLDLOG")}
                {SUAP_Response.render_code("MSMTCH")}
                {SUAP_Response.render_code("UNKACC")}
        """
        self.type = "LOGN"

        # Check if account with such username exists
        if not DB.account_exists(username):
            return SUAP_Response.UNKACC(
                f"Username {username} doesn't exist, please register first"
            )

        # Check if the password is correct
        if not DB.validate_user(username, password):
            return SUAP_Response.MSMTCH(f"Invalid username or password")

        # Check if the user is already logged in
        user=DB.find('user',{'is_active':1,'username':username})
        if len(user):
            # Check if the user is logged in from the same address
            if user[0].get('ip')==requset.ip: # requset.ip is to be replaces
                return SUAP_Response.OLDLOG(f"User {username} is already logged in")

            # Logout the user from the previous address
            DB.deactivate_user(username)

            # Login the user using the current address
            DB.activate_user(username, self.connection)

            # Return a Response object
            return SUAP_Response.NEWLOG(
                f"User {username} logged in successfully", data=DB_ret
            )

        # Log in the user
        DB_ret = DB.login(username)

        # Return a Response object
        return SUAP_Response.NEWLOG(
            f"User {username} logged in successfully", data=DB_ret
        )

    def _handle_is_logged_in_request(self, username: str, key: str) -> SUAP_Response:
        f"""Verifies the current login status of the client.

        Returns
        -------
        SUAP_Response
            Returns a SUAP_Response with codes:
                {SUAP_Response.render_code("OLDLOG")}
                {SUAP_Response.render_code("INTCPT")}
                {SUAP_Response.render_code("UNKACC")}
        """
        self.type = "LGDN"

        # Check if account with such username exists
        if not DB.account_exists(username):
            return SUAP_Response.UNKACC(
                f"Username {username} doesn't exist, please register first"
            )

        # Check if the user is already logged in
        if DB.is_logged_in(username):
            # Check if the user is logged in from the same address
            if DB.is_logged_in_from(username, self.connection):
                return SUAP_Response.OLDLOG(f"User {username} is logged in")

            # Return a Response object
            return SUAP_Response.INTCPT(
                f"User {username} is not logged in from this address"
            )

        # Return a Response object that user is not logged in
        return SUAP_Response.LGDOUT(f"User {username} is not logged in")

    def _handle_clear_session_request(self, username: str) -> SUAP_Response:
        f"""Clears the session of the user with the provided username.

        Returns
        -------
        SUAP_Response
            Returns a SUAP_Response with codes:
                {SUAP_Response.render_code("LGDOUT")}
                {SUAP_Response.render_code("INTCPT")}
                {SUAP_Response.render_code("UNKACC")}
                {SUAP_Response.render_code("LGDOUT")}
        """
        self.type = "CLRS"

        # Check if account with such username exists
        if not DB.account_exists(username):
            return SUAP_Response.UNKACC(
                f"Username {username} doesn't exist, please register first"
            )

        # Check if the user is already logged in
        if DB.is_logged_in(username):
            # Check if the user is logged in from the same address
            if DB.is_logged_in_from(username, self.connection):
                # Logout the user
                DB.logout(username)

                # Return a Response object
                return SUAP_Response.LGDOUT(f"User {username} logged out successfully")

            # Return a Response object
            return SUAP_Response.INTCPT(
                f"User {username} is not logged in from this address, please login first"
            )

        # Return a Response object that user is not logged in
        return SUAP_Response.LGDOUT(f"User {username} is not logged in")

    def __init__(self, connection):
        self.connection = connection
        self.type = None


