import __init__
import sqlite3
from pathlib import Path

from p2pchat.utils.utils import dict_factory


class ServerDB:
    """Server Database

    This class is used to interact with the server database"""

    def __init__(self):
        self.connection = sqlite3.connect(
            Path(Path(__file__).parent, "server.db"), check_same_thread=False
        )
        self.connection.row_factory = dict_factory
        self.cursor = self.connection.cursor()

    def create_chat_table(self):
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS chats (
                _id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                created_at REAL NOT NULL,
                last_updated REAL NOT NULL
            );
            """
        )
        self.connection.commit()

    def create_messages_table(self):
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                _id TEXT PRIMARY KEY,
                chat_id TEXT NOT NULL,
                sender TEXT NOT NULL,
                receiver TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at REAL NOT NULL
            );
            """
        )
        self.connection.commit()
