import __init__
from p2pchat.utils.utils import clear_console
def print_and_remember(*args,ending_line=None):
    text = ' '.join([str(arg) for arg in args])
    history.append(text)
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
            print(msg)
        if ending_line:
            print(ending_line,end="")
history=History()

