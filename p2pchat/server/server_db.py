import sqlite3



class ServerDB:
    """
    a class that contains all the server database related functions
    """
    def __init__(self):
        self.connection=sqlite3.connect("p2pchat.db")
        self.cursor=self.connection.cursor()
        self.create_user_table()
        
    def create_user_table(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            _id TEXT PRIMARY KEY,
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 0, 
            IP TEXT,
            created_at TEXT,
        );
        """)
        self.cursor.commit()

    def activate_user(self,username,ip):
        """
        sets a user status to active and updates their ip
        """
        self.cursor.execute("UPDATE users SET is_active = 1, IP = ? WHERE username = ?;",(username,ip))
        self.cursor.commit()

    def deactivate_user(self,username):
        """
        sets a user status to inactive
        """
        self.cursor.execute( "UPDATE users SET is_active = 0 WHERE username = ?;",(username))
        self.cursor.commit()
    
    def register_user(self,username,password):
        self.cursor.execute("INSERT INTO users (username, password, created_at) VALUES (?, ?, ?);",(username,password))
        self.cursor.commit()

    def account_exists(self,username):
        """
        checks if a username exists in the database return true if it exists
        """
        self.cursor.execute("SELECT * FROM users WHERE username = ?;",(username)).fetchone() is not None
   
    def find(self,table_name,attrs:dict)->list:
        """
        returns a list of users that match the attrs
        dict: {attribute:value}
        """
        table_attrs=self.get_table_columns(table_name)
        valid_attrs=[attr for attr in attrs if attr in table_attrs]
        if len(valid_attrs)==0:
            return []
        query=','.join([f"{valid_attr,attrs[valid_attr]}" for valid_attr in valid_attrs])        
        self.cursor.execute(f"SELECT * FROM {table_name} WHERE  {query};")
        return self.cursor.fetchall()

    def get_table_columns(self,table_name):
        try:
            res= self.cursor.execute("SELECT * FROM ? ",(table_name))
            return [member[0] for member in self.cursor.description]
        except:
            print("couldn't fetch names of columns")
            return 0
    
    def validate_user(self,username,password):
        """
        returns a user if it exists in the database
        """
        self.cursor.execute("SELECT * FROM USER WHERE username=? , password=?;",(username,password))
        return self.cursor.fetchone()
    
    def get_active_peers():
        pass
    