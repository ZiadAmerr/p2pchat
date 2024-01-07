import unittest
from unittest.mock import patch
from server_db import ServerDB

class TestServerDB(unittest.TestCase):
    def setUp(self):
        self.db = ServerDB()
        self.db.create_user_table()
        self.db.cursor.execute("DELETE FROM users")
        self.db.connection.commit()

    def tearDown(self):
        self.db.cursor.execute("DELETE FROM users")
        self.db.connection.commit()

    def test_account_exists(self):
        self.db.register_user("mohamed", "1234")
        self.assertTrue(self.db.account_exists("mohamed"))
        self.assertFalse(self.db.account_exists("non_existent_user"))

    def test_register_user(self):
        initial_count = len(self.db.get_active_peers())
        self.db.register_user("new_user", "password")
        updated_count = len(self.db.get_active_peers())
        
        # Debugging output
        print(f"Initial Count: {initial_count}")
        print(f"Updated Count: {updated_count}")
        
        # Fetching users for debugging
        print(f"Active Peers: {self.db.get_active_peers()}")

        self.assertEqual(updated_count, initial_count + 1)

    def test_login_logout(self):
        self.db.register_user("mohamed", "1234")

        with patch('server_db.utils.get_timesamp') as mock_timestamp:
            mock_timestamp.return_value = 123456789.0

            self.db.login("mohamed", "192.168.1.1", 8080)
            active_peers = self.db.get_active_peers()
            self.assertIn("mohamed", [user['username'] for user in active_peers])

            self.db.logout("mohamed")
            active_peers_after_logout = self.db.get_active_peers()
            self.assertNotIn("mohamed", [user['username'] for user in active_peers_after_logout])

    def test_set_last_seen(self):
        self.db.register_user("mohamed", "1234")
        self.db.set_last_seen("mohamed")
        user = self.db.validate_user("mohamed", "1234")
        self.assertIsNotNone(user)
        self.assertNotEqual(user['last_seen'], 0.0)

if __name__ == '__main__':
    unittest.main()
