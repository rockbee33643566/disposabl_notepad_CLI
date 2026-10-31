import sqlite3
from sqlite3 import Connection
from contextlib import contextmanager
from typing import Generator
import os

from schemas import user, message

@contextmanager
def get_conn(
    path: str | None = None,
    commit: bool = False    
) -> Generator[Connection, None, None]:
    if path is None:
        path = os.path.join("data", "database.db")
        
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row

    try:
        yield conn
    except Exception:
        conn.rollback()
        raise
    else:
        if commit:
            conn.commit()
    finally:
        conn.close()

def init_db() -> None: 
    with get_conn(commit=True) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNGUE, 
                user_name TEXT, 
                hash TEXT UNQUE
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS
                messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender_id INTEGER,
                    text TEXT,
                    TIME REAL,
                    used_notepad INTEGER,
                    is_readed INTEGER CHECK (is_readed IN (0, 1))
                )
        ''')

def create_user(usr: user.CreateUserPost, user_id: int) -> None:
    with get_conn(commit=True) as conn:
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO users(user_id, user_name, hash)
            VALUES
                (?, ?, ?)
            ''', 
            (user_id, usr.name, usr.hash)
        )
        