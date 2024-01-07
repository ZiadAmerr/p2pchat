import queue
from typing import List
import __init__
import sqlite3
from pathlib import Path
from p2pchat.utils.utils import (
    exception_wrapper,
    dict_factory,
    get_unique_id,
    get_timesamp,
)
import logging
import threading

logging.basicConfig(level=logging.INFO)
# Decorator function to apply color to text


FETCHALL = 0
FETCHONE = 1
FETCHMANY = 2
EXECUTE = 3


class SQLiteConnectionPool:
    def __init__(self, max_connections=5):
        self.max_connections = max_connections
        self._connections = queue.Queue(maxsize=max_connections)
        self._lock = threading.Lock()

        for _ in range(max_connections):
            connection = sqlite3.connect(
                Path(Path(__file__).parent, "server.db"), check_same_thread=False
            )
            connection.row_factory = dict_factory

            self._connections.put(connection)

    def get_connection(self):
        return self._connections.get()

    def release_connection(self, connection):
        if self._connections.full():
            connection.close()
        else:
            self._connections.put(connection)

    def execute(self, query, parameters=None, return_type=EXECUTE):
        connection = self.get_connection()
        cursor = connection.cursor()

        exc = None
        if parameters:
            exc = cursor.execute(query, parameters)
        else:
            exc = cursor.execute(query)

        connection.commit()
        if return_type == FETCHALL:
            result = cursor.fetchall()
        elif return_type == FETCHONE:
            result = cursor.fetchone()
        elif return_type == EXECUTE:
            result = exc

        cursor.close()
        self.release_connection(connection)
        return result


class ServerDB:
    """
    a class that contains all the server database related functions
    """

    def __init__(self, max_connections=100):
        self.connection_pool = SQLiteConnectionPool(max_connections)
        self.create_user_table()
        self.create_chatrooms_table()
        self.create_chatroom_users_table()

    @exception_wrapper
    def create_user_table(self):
        self.connection_pool.execute(
            """
        CREATE TABLE IF NOT EXISTS users (
            _id TEXT PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 0, 
            last_seen REAL NOT NULL DEFAULT 0,
            IP TEXT,
            PORT INTEGER,
            PORT_UDP INTEGER,
            created_at REAL NOT NULL,
            UNIQUE(IP,PORT)
        );
        """
        )

    @exception_wrapper
    def create_chatroom_users_table(self):
        self.connection_pool.execute(
            """
        CREATE TABLE IF NOT EXISTS chatroom_users (
            chatroom_key TEXT ,
            user_id TEXT,
            is_owner INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY(chatroom_key) REFERENCES chatrooms(key)
            FOREIGN KEY(user_id) REFERENCES users(_id)
            UNIQUE(user_id,chatroom_key)

        );
        """
        )

    @exception_wrapper
    def create_chatrooms_table(self):
        self.connection_pool.execute(
            """CREATE TABLE IF NOT EXISTS chatrooms(_id TEXT PRIMARY KEY,key TEXT UNIQUE);"""
        )

    @exception_wrapper
    def get_chatroom_users(self, chatroom_key):
        return self.connection_pool.execute(
            f"""
                SELECT u.username,u.is_active,u.PORT,u.IP,cu.is_owner,cu.chatroom_key FROM users u
                INNER JOIN chatroom_users cu ON u._id=cu.user_id
                INNER JOIN chatrooms c ON c.key=cu.chatroom_key
                WHERE c.key= ? ;""",
            (chatroom_key,),
            return_type=FETCHALL,
        )

    @exception_wrapper
    def get_chatrooms_admins(self):
        return self.connection_pool.execute(
            f"""
                SELECT u.username as owner,u.is_active,u.PORT,u.IP,cu.is_owner,c.key FROM users u
                INNER JOIN chatroom_users cu ON u._id=cu.user_id
                INNER JOIN chatrooms c ON c.key=cu.chatroom_key
                WHERE cu.is_owner=1;""",
            return_type=FETCHALL,
        )

    def create_chatroom(self, chatroom_key, user_id):
        chat_room_id = get_unique_id()
        self.connection_pool.execute(
            """
        INSERT INTO chatrooms (_id,key) VALUES (?,?);
        """,
            (chat_room_id, chatroom_key),
        )
        self.connection_pool.execute(
            """
        INSERT INTO chatroom_users (chatroom_key,user_id,is_owner) VALUES (?,?,1);
        """,
            (chatroom_key, user_id),
        )

    @exception_wrapper
    def join_chatroom(self, chatroom_key, user_id):
        self.connection_pool.execute(
            """
        INSERT INTO chatroom_users (chatroom_key,user_id) VALUES (?,?);
        """,
            (chatroom_key, user_id),
        )

    @exception_wrapper
    def login(self, username, ip, port, udp_port):
        """
        sets a user status to active and updates their ip
        """
        res = self.connection_pool.execute(
            f"UPDATE users SET is_active = 1, IP = ?, PORT = ?, last_seen = {get_timesamp()}, PORT_UDP = ? WHERE username = ?;",
            (ip, port, udp_port, username),
            return_type=EXECUTE,
        )
        return res

    @exception_wrapper
    def logout(self, username):
        """
        sets a user status to inactive
        """

        self.connection_pool.execute(
            "UPDATE users SET is_active = 0, last_seen = 0 WHERE username = ?;",
            (username,),
        )

    @exception_wrapper
    def register_user(self, username, password):
        self.connection_pool.execute(
            "INSERT INTO users (_id,username, password, created_at) VALUES (?, ?, ?, ?);",
            (get_unique_id(), username, password, get_timesamp()),
        )

    @exception_wrapper
    def account_exists(self, username):
        """
        checks if a username exists in the database return true if it exists
        """
        return (
            self.connection_pool.execute(
                "SELECT * FROM users WHERE username = ?;",
                (username,),
                return_type=FETCHONE,
            )
            is not None
        )

    @exception_wrapper
    def find(self, table_name, attrs: dict) -> list:
        """
        returns a list of users that match the attrs
        dict: {attribute:value}
        """
        table_attrs = self.get_table_columns(table_name)
        valid_attrs = [attr for attr in attrs.keys() if attr in table_attrs]
        valid_vals = [attrs[attr] for attr in valid_attrs]
        if len(valid_attrs) == 0 and len(attrs):
            logging.debug(
                f"Invalid attrs provided, valid table attrs are: {table_attrs}"
            )
            return []

        conditions = " AND ".join([f"{valid_attr}=?" for valid_attr in valid_attrs])
        query = f"SELECT * FROM {table_name} WHERE {conditions};"
        return self.connection_pool.execute(
            query, tuple(valid_vals), return_type=FETCHALL
        )

    @exception_wrapper
    def get_table_columns(self, table_name):
        try:
            conn = self.connection_pool.get_connection()
            cursor = conn.cursor()
            res = cursor.execute(f"SELECT * FROM {table_name} ;")
            cols = [member[0] for member in cursor.description]
            cursor.close()
            self.connection_pool.release_connection(conn)
            return cols
        except Exception as e:
            print("couldn't fetch names of columns: ", e)
            return []

    @exception_wrapper
    def validate_user(self, username, password):
        """
        returns a user if it exists in the database
        """
        return self.connection_pool.execute(
            "SELECT * FROM users WHERE username=? and password=?;",
            (
                username,
                password,
            ),
            return_type=FETCHONE,
        )

    @exception_wrapper
    def get_active_peers(self):
        """modify later to only include important fileds"""
        return self.connection_pool.execute(
            "SELECT * FROM users WHERE is_active!=0", return_type=FETCHALL
        )

    @exception_wrapper
    def set_last_seen(self, username):
        """
        sets the last seen of a user to the current time
        """
        self.connection_pool.execute(
            f"UPDATE users SET last_seen = {get_timesamp()} WHERE username = '{username}';"
        )

    @exception_wrapper
    def is_room_owner(self, chatroom_key, user_id):
        """
        checks if a user is a room owner
        """

        return (
            self.connection_pool.execute(
                f"SELECT * FROM chatroom_users WHERE chatroom_key = '{chatroom_key}' AND user_id = '{user_id}' AND is_owner = 1;",
                return_type=FETCHONE,
            )
            is not None
        )

    @exception_wrapper
    def get_chatroom_members(self, chatroom_key):
        return self.connection_pool.execute(
            f"""
                SELECT u.username as username,u.is_active,u.PORT,u.PORT_UDP as PORT_UDP,u.IP,c.key FROM users u
                INNER JOIN chatroom_users cu ON u._id=cu.user_id
                INNER JOIN chatrooms c ON c.key=cu.chatroom_key
                WHERE c.key=?;""",
            (chatroom_key,),
            return_type=FETCHALL,
        )


myDB = ServerDB()
# demo
if __name__ == "__main__":
    db = ServerDB()
    # print(db.create_chatrooms_table())
    # print(db.create_chatroom_users_table())
    # db.create_user_table()
    # db.register_user("mohamed", "1234")
    # db.register_user("mohamed1", "123")
    """ print(db.get_active_peers())
    print(db.account_exists("mohamed"))
    print(db.validate_user("mohamed", "123"))
    print(db.validate_user("mohamed", "1234"))
    db.login("mohamed", "192.168.1.1")
    print(db.get_active_peers())
    db.logout("mohamed")
    print(db.get_active_peers())
    print(db.validate_user("mohamed", "123"))
    print(db.find("users", {"useraname": "mohamed"}))
    print(db.find("users", {"is_active": 1})) """

    # print(db.get_chatroom_users("test_ch"))
    user = db.find("users", {"username": "mohamed"})[0]
    print(user)
    print(db.create_chatroom("test_ch", user["_id"]))
    print(db.get_chatroom_users("test_ch"))
    user = db.find("users", {"username": "mohamed1"})[0]
    print(db.join_chatroom("test_ch", user["_id"]))
    print(db.get_chatroom_users("test_ch"))
    print(db.get_chatrooms_admins())
    print(db.get_chatroom_members("af"))
    print(db.get_chatroom_members("aa"))
    print(db.get_chatroom_members("test3"))
