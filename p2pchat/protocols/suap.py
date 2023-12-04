from ..server.db import DB


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
        24: ("LGDOUT", "user is not logged in"),
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

    def __init__(self, code: int, message: str, is_success: bool, data=None) -> None:
        self.code = code
        self.message = message
        self.is_success = is_success
        self.data = data if isinstance(data, dict) else {}

    @staticmethod
    def NEWLOG(message: str, data) -> "SUAP_Response":
        return SUAP_Response(10, message, True, data)

    @staticmethod
    def OLDLOG(message: str) -> "SUAP_Response":
        return SUAP_Response(11, message, True)

    @staticmethod
    def NEWREG(message: str) -> "SUAP_Response":
        return SUAP_Response(12, message, True)

    @staticmethod
    def LGDOUT(message: str) -> "SUAP_Response":
        return SUAP_Response(13, message, True)

    @staticmethod
    def MSMTCH(message: str) -> "SUAP_Response":
        return SUAP_Response(20, message, False)

    @staticmethod
    def CNFLCT(message: str) -> "SUAP_Response":
        return SUAP_Response(21, message, False)

    @staticmethod
    def UNKACC(message: str) -> "SUAP_Response":
        return SUAP_Response(22, message, False)

    @staticmethod
    def INTCPT(message: str) -> "SUAP_Response":
        return SUAP_Response(23, message, False)

    def __str__(self) -> str:
        return f"{self.code} {self.message}"

    def __repr__(self) -> str:
        return f"<SUAP_Response code={self.code} message={self.message} is_success={self.is_success} data={self.data}>"

    def __dict__(self) -> dict:
        return {
            "code": self.code,
            "message": self.message,
            "is_success": self.is_success,
            "data": self.data,
        }

    @staticmethod
    def init_from_dict(data: dict) -> "SUAP_Response":
        return SUAP_Response(
            data["code"], data["message"], data["is_success"], data["data"]
        )


class SUAP_Request:
    types = {"RGST", "LOGN", "LGDN", "CLRS"}

    def __init__(self, connection):
        self.connection = connection
        self.type = None

    def rgst_request(self, username: str, password: str) -> SUAP_Response:
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
            return SUAP_Response.CNFLCT(
                f"Username {username} already exists, please choose another one"
            )

        # Create an account
        DB.create_account(username, password)

        # Return a Response object
        return SUAP_Response.NEWREG(f"Account {username} created successfully")

    def login_request(self, username: str, password: str) -> SUAP_Response:
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
        if not DB.check_password(username, password):
            return SUAP_Response.MSMTCH(f"Password for {username} is incorrect")

        # Check if the user is already logged in
        if DB.is_logged_in(username):
            # Check if the user is logged in from the same address
            if DB.is_logged_in_from(username, self.connection):
                return SUAP_Response.OLDLOG(f"User {username} is already logged in")

            # Logout the user from the previous address
            DB.logout(username)

            # Login the user using the current address
            DB.login(username, self.connection)

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

    def is_logged_in_request(self, username: str, key: str) -> SUAP_Response:
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

    def clear_session_request(self, username: str) -> SUAP_Response:
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


def main():
    from ..server.connection import Connection

    conn = Connection("localhost", 8000)

    req = SUAP_Request(conn)

    print(req.rgst_request("user", "pass"))

    print(req.login_request("user", "pass"))

    print(req.is_logged_in_request("user", "key"))

    print(req.clear_session_request("user"))


if __name__ == "__main__":
    main()
