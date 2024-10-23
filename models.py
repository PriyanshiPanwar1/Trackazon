import sqlite3
from flask import current_app

class User:
    def __init__(self, username, password):
        self.username = username
        self.password = password

    @staticmethod
    def create_table():
        conn = sqlite3.connect(current_app.config['DATABASE'])
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

    @staticmethod
    def add_user(username, password):
        try:
            conn = sqlite3.connect(current_app.config['DATABASE'])
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
        except sqlite3.IntegrityError:
            return False  # User already exists
        finally:
            conn.close()
        return True

    @staticmethod
    def get_user(username):
        conn = sqlite3.connect(current_app.config['DATABASE'])
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()
        return user

class PriceHistory:
    def __init__(self, product_name, price):
        self.product_name = product_name
        self.price = price

    @staticmethod
    def create_table():
        conn = sqlite3.connect(current_app.config['DATABASE'])
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT NOT NULL,
                price REAL NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

    @staticmethod
    def add_price_history(product_name, price):
        conn = sqlite3.connect(current_app.config['DATABASE'])
        cursor = conn.cursor()
        cursor.execute("INSERT INTO price_history (product_name, price) VALUES (?, ?)", (product_name, price))
        conn.commit()
        conn.close()

    @staticmethod
    def get_price_history(product_name):
        conn = sqlite3.connect(current_app.config['DATABASE'])
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM price_history WHERE product_name = ?", (product_name,))
        history = cursor.fetchall()
        conn.close()
        return history
