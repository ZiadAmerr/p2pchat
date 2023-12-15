"""
this file will be used to add cli featrues such as logging, coloring, etc
"""
from logging import Logger

class CustomLogger(Logger):
    pass

app_logger= CustomLogger("app_logger")