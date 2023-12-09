import __init__
import sqlite3
import datetime
from pathlib import Path
from p2pchat.utils import utils
import logging
logging.basicConfig(level=logging.DEBUG)
class ServerDB:
    """
    a class that contains all the server database related functions
    """
    def __init__(self):
        self.connection=sqlite3.connect(Path(Path(__file__).parent , 'server.db'),check_same_thread=False)
        self.connection.row_factory=utils.dict_factory
        self.cursor=self.connection.cursor()
        self.create_user_table()
        
    def create_user_table(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            _id TEXT PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 0, 
            last_seen REAL NOT NULL DEFAULT 0,
            IP TEXT UNIQUE,
            created_at REAL NOT NULL
        );
        """)
        self.connection.commit()

    def login(self,username,ip):
        """
        sets a user status to active and updates their ip
        """
        res=self.cursor.execute("UPDATE users SET is_active = 1, IP = ? WHERE username = ?;",(ip,username))
        self.set_last_seen(username) # may merge both steps later
        self.connection.commit()
        return res

    def logout(self,username):
        """
        sets a user status to inactive
        """
        
        self.cursor.execute(f"UPDATE users SET is_active = 0 WHERE username = '{username}';",)
        self.connection.commit()
    
    def register_user(self,username,password):
        try:
            self.cursor.execute("INSERT INTO users (_id,username, password, created_at) VALUES (?,?, ?, ?);",
                                (utils.get_unique_id(),username,password,utils.get_timesamp()))
            self.connection.commit()
        except Exception as e:
            print ("an error occured : ",e)
    def account_exists(self,username):
        """
        checks if a username exists in the database return true if it exists
        """
        return self.cursor.execute("SELECT * FROM users WHERE username = ?;",(username,)).fetchone() is not None
   
    def find(self,table_name,attrs:dict)->list:
        """
        returns a list of users that match the attrs
        dict: {attribute:value}
        """
        table_attrs=self.get_table_columns(table_name)
        valid_attrs=[attr for attr in attrs.keys() if attr in table_attrs]
        if len(valid_attrs)==0 and len(attrs):
            logging.debug(f'Invalid attrs provided, valid table attrs are: {table_attrs}')
            return []
        
        conditions=' AND '.join([f"{valid_attr}=?" for valid_attr in valid_attrs])        
        query=f"SELECT * FROM {table_name} WHERE {conditions};"
        self.cursor.execute(query,tuple(attrs.values()))
        return self.cursor.fetchall()

    def get_table_columns(self,table_name):
        try:
            res= self.cursor.execute(f"SELECT * FROM {table_name} ;")
            return [member[0] for member in self.cursor.description]
        except Exception as e:
            print("couldn't fetch names of columns: ",e)
            return []
    
    def validate_user(self,username,password):
        """
        returns a user if it exists in the database
        """
        self.cursor.execute("SELECT * FROM users WHERE username=? and password=?;",(username,password,))
        return self.cursor.fetchone()
    
    def get_active_peers(self):
        """modify later to only include important fileds"""
        self.cursor.execute("SELECT * FROM users WHERE is_active!=0")
        return self.cursor.fetchall()
 
    def _execute(self,command,commit=False):
        """
        executes a command and returns the result, internal uses only!!
        """
        res=self.cursor.execute(command)
        if commit:
            self.connection.commit()
        return res
    def set_last_seen(self,username):
        """
        sets the last seen of a user to the current time
        """
        self.cursor.execute(f"UPDATE users SET last_seen = {utils.get_timesamp()} WHERE username = '{username}';")
        self.connection.commit()
myDB=ServerDB()
#demo
if __name__=='__main__':
    db=ServerDB()
    db.create_user_table()
    db.register_user('mohamed','1234')
    db.register_user('mohamed1','123')
    print(db.get_active_peers())
    print(db.account_exists('mohamed'))
    print(db.validate_user('mohamed','123'))
    print(db.validate_user('mohamed','1234'))
    db.login('mohamed','192.168.1.1')
    print(db.get_active_peers())
    db.logout('mohamed')
    print(db.get_active_peers())
    print(db.validate_user('mohamed','123'))
    print(db.find('users',{'useraname':'mohamed'}))
    print(db.find('users',{'is_active':1}))
