import sqlite3
from datetime import datetime

DB_NAME = 'messages.db'

class MessageRepository:
    @staticmethod
    def init_db():
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER NOT NULL,
                receiver_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                is_read BOOLEAN NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

    @staticmethod
    def save_message(data):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''
            INSERT INTO messages (sender_id, receiver_id, message, is_read, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            data['sender_id'],
            data['receiver_id'],
            data['message'],
            int(data['is_read']),
            data['created_at']
        ))
        conn.commit()

        message_id = c.lastrowid
        conn.close()

        return {
            "id": message_id,
            **data
        }

# Optional: Initialize the database when the module is imported
MessageRepository.init_db()
