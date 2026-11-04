from sqlcipher3 import dbapi2

from sqlite3 import Connection, Row
from contextlib import contextmanager
from typing import Generator
from pathlib import Path

from .schemas import user, message
from .encryption.encryption import get_db_key

@contextmanager
def get_conn(
    path: str | None = None,
    commit: bool = False    
) -> Generator[Connection, None, None]:
    if path is None:
        path = str(
            Path(__file__).parent.parent / "data" / "database.db"
        )

    conn: Connection
    conn = dbapi2.connect(path)

    try:
        conn.row_factory = dbapi2.Row

        cursor = conn.cursor()
        cursor.execute(f'''--sql
            PRAGMA key = '{get_db_key()}'
        ''')
        cursor.close()
        
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
        conn.execute('''--sql
            CREATE TABLE IF NOT EXISTS 
                users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL UNIQUE, 
                    user_name TEXT, 
                    hash TEXT UNIQUE
                )
        ''')

        conn.execute('''--sql
            CREATE TABLE IF NOT EXISTS
                contacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    master_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL, 
                    name TEXT
                )
        ''')

        conn.execute('''--sql
            CREATE TABLE IF NOT EXISTS
                sendet_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recipient_id INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    time INTEGER NOT NULL,
                    used_notepad INTEGER,
                    is_readed INTEGER DEFAULT 0 CHECK (is_readed IN (0, 1))
                )
        ''')

        conn.execute('''--sql
            CREATE TABLE IF NOT EXISTS
                received_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender_id INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    time INTEGER,
                    used_notepad INTEGER,
                    is_readed INTEGER DEFAULT 0 CHECK (is_readed IN (0, 1))
                )
        ''')

def create_user(usr: user.CreateUserPost, user_id: int) -> None:
    with get_conn(commit=True) as conn:
        cursor = conn.cursor()

        cursor.execute('''--sql
            INSERT INTO users (user_id, user_name, hash)
            VALUES
                (?, ?, ?)
            ''', 
            (user_id, usr.name, usr.hash)
        )

def get_user_hash(id: int) -> str:
    with get_conn() as conn: 
        cursor = conn.cursor()

        cursor.execute('''
            SELECT hash FROM users WHERE id = ?
            ''',
            (id, )
        )

        row = cursor.fetchone()
    return row["hash"]

def get_accounts() -> user.Accounts | None:
    with get_conn() as conn:
        cursor = conn.cursor()

        cursor.execute('''--sql
            SELECT id, user_id, user_name, hash FROM users
        ''')

        row = cursor.fetchall()

    if not row:
        return None
    else:
        return user.Accounts(accounts=[dict(i) for i in row])

def add_received_messages(msg: message.MessagesGet) -> None:
    data = [
        (msg.sender_id, 
        msg.text, 
        msg.time, 
        msg.used_notepad) 
        for msg in msg.messages
    ]

    with get_conn(commit=True) as conn:
        cursor = conn.cursor()

        cursor.executemany('''--sql
            INSERT INTO users (
                sender_id, 
                text, 
                time, 
                used_notepad, 
            )
            VALUES
                (?, ?, ?, ?)
            ''',
            data
        )

def add_sendet_message(msg: message.SendedMessage) -> None:
    data = [
        msg.recipient_id, msg.text, msg.time, msg.used_notepad, 1
    ]

    with get_conn(commit=True) as conn:
        cursor = conn.cursor()

        cursor.execute('''--sql
            INSERT INTO sendet_messages (
                recipient_id, 
                text, 
                time, 
                used_notepad, 
                is_readed
            )
            VALUES
                (?, ?, ?, ?, ?)
            ''',
            data
        )

def add_contact(user_local_id: int, user_id: int, name: str) ->  None: 
    with get_conn(commit=True) as conn: 
        cursor = conn.cursor()
        cursor.execute('''--sql
            INSERT INTO contacts (
                user_id, 
                master_id,
                name
            )
            VALUES
                (?, ?, ?)
            ''',
            (user_id, user_local_id, name)
        )

def get_contact(user_id: int) -> user.Accounts | None:
    with get_conn() as conn: 
        cursor = conn.cursor()
        cursor.execute('''--sql
            SELECT user_id, name FROM contacts 
            WHERE master_id = ?
            ''', 
            (user_id, )
        )

        row = cursor.fetchall()

    if not row: 
        return None
    else: 
        return user.Contacts(contacts=[dict(i) for i in row])


# ===== AI =====
def get_history(user_id: int, peer_id: int) -> list[message.SendedMessage]:
    with get_conn() as conn:
        cursor = conn.cursor()

        cursor.execute('''--sql
            SELECT sender_id, text, time, used_notepad FROM received_messages
            WHERE sender_id = ?
        ''', (peer_id,))
        incoming = [message.Message(**dict(r)) for r in cursor.fetchall()]
        
        cursor.execute('''--sql
            SELECT recipient_id, text, time, used_notepad FROM sendet_messages
            WHERE recipient_id = ?
        ''', (user_id,))
        outgoing = [message.SendedMessage(**dict(r)) for r in cursor.fetchall()]

    combined = incoming + outgoing
    combined.sort(key=lambda m: m.time)
    return combined