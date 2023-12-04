from pymongo import MongoClient


class SUAP_Response:
    success_codes = {
        10: ("NEWLOG", "login is successful"),
        11: ("OLDLOG", "user is already logged in"),
        12: ("NEWREG", "register is successful"),
        13: ("LGDOUT", "logout is successful"),
    }

    failure_codes = {
        20: ("MSMTCH", "username-password mismatch"),
        21: ("CNFLCT", "username already exists in database"),
        22: ("UNKACC", "username wasn't found in database"),
        23: ("INTCPT", "the request seems to be intercepted"),
    }

    all_codes = {
        **success_codes,
        **failure_codes,
    }

    @staticmethod
    def get_code(str_code: str) -> int:
        """Returns the int code from the str code, -1 otherwise"""
        # Search for the code
        for code, (str_code_, code_def) in SUAP_Response.all_codes.items():
            if str_code_ == str_code:
                return code
        
        # Otherwise
        raise NotImplementedError(f"Code {str_code} is not currently supported")

    @staticmethod
    def render_code(str_code: str) -> str:
        # Get the code
        code = SUAP_Response.get_code(str_code)

        alias, description = SUAP_Response.all_codes[code]

        return f"{code} {alias} when {description.lower()}"
    

# Includes database operations
class DB:
    # db initializations
    def __init__(self):
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client['p2p-chat']


    # checks if an account with the username exists
    def is_account_exist(self, username):
        if self.db.accounts.find({'username': username}).count() > 0:
            return True
        else:
            return False
    

    # registers a user
    def register(self, username, password):
        account = {
            "username": username,
            "password": password
        }
        self.db.accounts.insert(account)


    # retrieves the password for a given username
    def get_password(self, username):
        return self.db.accounts.find_one({"username": username})["password"]


    # checks if an account with the username online
    def is_account_online(self, username):
        if self.db.online_peers.find({"username": username}).count() > 0:
            return True
        else:
            return False

    
    # logs in the user
    def user_login(self, username, ip, port):
        online_peer = {
            "username": username,
            "ip": ip,
            "port": port
        }
        self.db.online_peers.insert(online_peer)
    

    # logs out the user 
    def user_logout(self, username):
        self.db.online_peers.remove({"username": username})
    

    # retrieves the ip address and the port number of the username
    def get_peer_ip_port(self, username):
        res = self.db.online_peers.find_one({"username": username})
        return (res["ip"], res["port"])


class SUAP_Request:
    def __init__(self, connection):
        self.connection = connection

    def rgst_request(self, username: str, password: str) -> SUAP_Response:
        f"""Send a RGST (register) request

        Parameters
        ----------
        username: str

        
        Returns
        -------
        SUAP_Response
            Returns a SUAP_Response with codes:
                {SUAP_Response.render_code("NEWREG")}
                {SUAP_Response.render_code("CNFLCT")}
        """
        

    # RGST - Register
    # Syntax: RGST <<username>> <<password>>
    # Creates a new user account with the provided username and password.
    # - Returns 12 NEWREG: If the account is successfully created.
    # - Returns 21 CONFLICT: If the username is already in use.
    # LOGN - Log In
    # Syntax: LOGN <<username>> <<password>> <<key>
    # Attempts to authenticate the user with the provided username and password.
    # - Returns 10 NEWLOG: If successful.
    # - Returns 11 OLDLOG: Neglects data entered iff already authenticated.
    # - Returns 20 INCORRECTCREDS: If the username or password is incorrect.
    # - Returns 22 UNKNOWNACC: If the username doesn't belong to any account.
    # LGDN - Logged In
    # Syntax: LGDN <<username>> <<key>> Terminates the current authenticated session.
    # - Returns 11 OLDLOG: Already logged in
    # - Returns 23 INTERCEPT: If the username is logged in but bound to a different address
    # - Returns 22 UNKNOWNACC: If the username doesn't belong to any account
    # CLRS - Clear Session (Logout)
    # Syntax: CLRS <<username>> <<key>> Verifies the current login status of the client.
    # - Returns 13 LOGGEDOUT: If the log out is successful
    # - Returns 23 INTERCEPT: If the username is logged in but bound to a different address
    # - Returns 22 UNKNOWNACC: If the username doesn't belong to any account
    request_commands = {
        "RGST"
    }

    def __init__(request):
        pass



def main():
    code = SUAP_Response.get_code("INTCPT")
    print(code)


if __name__ == "__main__":
    main()