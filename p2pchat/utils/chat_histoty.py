import __init__
from p2pchat.utils.utils import clear_console

def print_and_remember(*args,ending_line=None):
    text = ' '.join([str(arg) for arg in args])
    history.append(text)
    clear_console()
    history.print_chat(ending_line)

def print_volatile_message(*args,ending_line=None):
    text = ' '.join([str(arg) for arg in args])
    history.append((text,'volatile'))
    clear_console()
    history.print_chat(ending_line)

class History:
    def __init__(self):
        self.history=[]
    def append(self,msg):
         self.history.append(msg)
    def reset_history(self):
        self.history=[]
    def print_chat(self,ending_line=None):
        for msg in self.history:
            print(msg if isinstance(msg,str) else msg[0])
        if ending_line:
            print(ending_line,end="")
    def clear_volatile_messages(self):
        self.history=[msg for msg in self.history if isinstance(msg,str) or msg[1]!='volatile']
history=History()

