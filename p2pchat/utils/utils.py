import datetime
import time 
import uuid
def get_timesamp():
    """ unix timestamp"""
    return time.mktime(datetime.datetime.now().timetuple())
def to_human_time(timestamp):
    """ user-friendly format"""
    return datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
def get_unique_id():
    return str(uuid.uuid4())
def validate_request(requset, required_fields):
    """ check if request contains all required fields"""
    for field in required_fields:
        if field not in requset:
            return False
    return True

def dict_factory(cursor, row):
    """ by default sqlite return qurey results as tuples,
      we override the connection.row_factory to convert sqlite3 rows to dicts for ease of access"""
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d
