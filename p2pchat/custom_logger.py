"""
this file will be used to add cli featrues such as logging, coloring, etc
"""
#TODO: make it work
import logging
class CustomLogger(logging.Logger):
    def __init__(self, name, level=logging.NOTSET):
        super().__init__(name, level)


app_logger= CustomLogger("app_logger")
server_logger=CustomLogger("server_logger")

