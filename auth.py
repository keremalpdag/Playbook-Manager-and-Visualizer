import sqlite3
import bcrypt

class Authenticator:
    def __init__(self, db_path='playbook_visualizer.db'):
        self.is_authenticated = False
        self.db_path = db_path

    def hash_password(self, password):
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        return hashed

    def verify_password(self, stored_password, provided_password):
        return bcrypt.checkpw(provided_password.encode('utf-8'), stored_password)

    def fetch_password(self, username):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT password FROM users WHERE username = ?', (username,))
        result = cursor.fetchone()
        conn.close()
        if result:
            return result[0]
        else:
            return None

    def authenticate(self, username, input_password):
        stored_password = self.fetch_password(username)
        if stored_password and self.verify_password(stored_password, input_password):
            self.is_authenticated = True
            return True
        else:
            return False
