import sqlite3

def initialize(path):
    with sqlite3.connect(path) as conn:
        conn.execute("create table if not exists items (key text)")

def create(path, key):
    with sqlite3.connect(path) as conn:
        conn.execute("insert into items(key) values (?)", (key,))
