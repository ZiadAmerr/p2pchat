import logging


class CustomLogger(logging.Logger):
    def __init__(self, name, level=logging.NOTSET):
        super().__init__(name, level)


app_logger = CustomLogger("app_logger")
server_logger = CustomLogger("server_logger")
