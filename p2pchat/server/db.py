from pymongo import MongoClient
from typing import Tuple
from dotenv import load_dotenv
import os
load_dotenv()


# Includes database operations
class DB:
    # db initializations
    def __init__(self):
        """
        Initializes the database
        currently we use an online mongodb server... maybe we can make it local in the future.
        client: (mongodb server client )
        db: the database itself, 
        
        you can access any tables in the database using the db object.
        db.user.insert({"username": "mohgir", "password": "1234"})
        db.user.find({"username": "mohgir"})
        etc...
        """
        self.client = MongoClient(f"mongodb+srv://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@cluster0.yluzmdm.mongodb.net/")
        self.db = self.client["p2p-chat"]

    def add_user(self, username, password):
        user = {"username": username, "password": password}
        self.db.users.insert(user)
    # checks if an account with the username exists
    def is_account_exist(self, username: str) -> bool:
        if self.db.accounts.find({"username": username}).count() > 0:
            return True
        else:
            return False

    # registers a user
    def register(self, username, password) -> None:
        account = {"username": username, "password": password}
        self.db.accounts.insert(account)

    # retrieves the password for a given username
    def get_password(self, username) -> str:
        return self.db.accounts.find_one({"username": username})["password"]

    # checks if an account with the username online
    def is_account_online(self, username) -> bool:
        if self.db.online_peers.find({"username": username}).count() > 0:
            return True
        else:
            return False

    # logs in the user
    def user_login(self, username, ip, port) -> None:
        online_peer = {"username": username, "ip": ip, "port": port}
        self.db.online_peers.insert(online_peer)

    # logs out the user
    def user_logout(self, username) -> None:
        self.db.online_peers.remove({"username": username})

    # retrieves the ip address and the port number of the username
    def get_peer_ip_port(self, username) -> Tuple[str, int]:
        res = self.db.online_peers.find_one({"username": username})
        return (res["ip"], res["port"])

if __name__ == "__main__":
    database= DB()
    database.add_user("mohgir", "12234")