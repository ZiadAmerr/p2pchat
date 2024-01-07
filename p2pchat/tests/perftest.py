import __init__
import p2pchat
from p2pchat.utils import utils, colors, chat_history
from p2pchat.server import (
    authentication_manager,
    monitor,
    request_handler,
    server_db,
    server,
)
from p2pchat.protocols import base_protocol, s4p, suap, tcp_request_transceiver
from p2pchat.peer import peer_client, peer_db, peer_server
from p2pchat import cli, custom_logger, data, globals

# loop through all utils functions

# def get_all_functions_from_module_recursive(module, max_depth=3, depth=0):
#     functions = []
#     if depth >= max_depth:
#         return functions
#     for func in module.__dict__.values():
#         if callable(func):
#             functions.append((func, depth))
#         elif hasattr(func, "__dict__"):
#             new_functions = get_all_functions_from_module_recursive(func, max_depth=max_depth, depth=depth+1)
#             functions.extend(new_functions)
#     return functions

# print("Testing utils module...")
# for func in get_all_functions_from_module_recursive(utils):
#     try:
#         print("Testing function: {}".format(func[0].__name__))
#     except:
#         print("Testing function: {}".format(func[0]))


def get_all_classes_from_module_recursive(module, max_depth=2, depth=0):
    classes = []
    if depth >= max_depth:
        return classes
    for cls in module.__dict__.values():
        if isinstance(cls, type):
            classes.append((cls, depth))
        elif hasattr(cls, "__dict__"):
            new_classes = get_all_classes_from_module_recursive(
                cls, max_depth=max_depth, depth=depth + 1
            )
            classes.extend(new_classes)
    return classes


for class_ in get_all_classes_from_module_recursive(p2pchat, max_depth=3):
    print(f"Testing class depth #{class_[1]}: {class_[0].__name__}")
