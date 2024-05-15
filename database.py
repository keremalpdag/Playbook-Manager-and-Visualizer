import sqlite3
import bcrypt

def create_database():
    conn = sqlite3.connect('playbook_visualizer.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS playbooks (
            id INTEGER PRIMARY KEY,
            incident_title TEXT NOT NULL,
            steps TEXT NOT NULL,
            category TEXT NOT NULL,
            criticality TEXT,
            criticality_description TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    cursor.execute("PRAGMA table_info(playbooks)")
    columns = [info[1] for info in cursor.fetchall()]
    if 'criticality' not in columns:
        cursor.execute('ALTER TABLE playbooks ADD COLUMN criticality TEXT')
    if 'criticality_description' not in columns:
        cursor.execute('ALTER TABLE playbooks ADD COLUMN criticality_description TEXT')

    admin_username = 'admin'
    admin_password = 'admin'
    hashed_password = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt())

    try:
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (admin_username, hashed_password))
    except sqlite3.IntegrityError:
        print("Admin account already exists.")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_database()
