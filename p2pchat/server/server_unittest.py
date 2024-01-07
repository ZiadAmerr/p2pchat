import pickle
import unittest
from unittest.mock import Mock
from server import UDPManager

class TestUDPManager(unittest.TestCase):
    def setUp(self):
        # Initialize UDPManager instance for testing
        self.udp_manager = UDPManager('127.0.0.1', 8888)
        self.mock_socket = Mock()
        self.udp_manager.server_socket = self.mock_socket

    def test_valid_request_handling(self):
        valid_request = pickle.dumps({"body": {"type": "some_type", "username": "user123"}})
        self.mock_socket.recvfrom.return_value = (valid_request, ('127.0.0.1', 1234))

        # Ensure the request is processed correctly
        with unittest.mock.patch('server.DB.set_last_seen') as mock_set_last_seen:
            self.udp_manager.handle_request()

        mock_set_last_seen.assert_called_once_with("user123")
        self.assertTrue(mock_set_last_seen.called, "Valid request handling passed successfully")
        print("Valid request handling passed successfully")  # Print a message after the test passes

    def test_invalid_request_handling(self):
        invalid_request = pickle.dumps({"body": {"wrong_key": "value"}})
        self.mock_socket.recvfrom.return_value = (invalid_request, ('127.0.0.1', 1234))

        # Ensure invalid request is logged
        with unittest.mock.patch('server.logging.warn') as mock_log_warn:
            self.udp_manager.handle_request()

        mock_log_warn.assert_called_once_with("invalid request")
        self.assertTrue(mock_log_warn.called, "Invalid request handling passed successfully")
        print("Invalid request handling passed successfully")  # Print a message after the test passes


if __name__ == '__main__':
    unittest.main()
