"""
this class is intended to monitor the clients
every 20 seconds, this monitor will check the last seen of all clients, deactiveate the inactive ones
"""
import threading
from p2pchat.server.server_db import myDB as DB
from utils.utils import get_timesamp
import time
class UsersMonitor(threading.Thread):
    def __init__(self, interval=20):
        super().__init__()
        self.interval = interval
        self.keep_monitoring = True
    def run(self):
        while not self.keep_monitoring:
            users=DB.find('users',{'is_active':1})
            for user in users:
                if user.get('last_seen') is None:
                    DB.deactivate_user(user.get('username'))
                if (get_timesamp()-user.get('last_seen'))>180:
                    DB.deactivate_user(user.get('username'))
            time.sleep(self.interval)
    def stop_monitoring(self):
        self.keep_monitoring=False