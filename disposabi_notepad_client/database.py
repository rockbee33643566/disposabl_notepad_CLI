from sqlcipher3 import dbapi2

from sqlite3 import Connection
from contextlib import contextmanager
from typing import Generator
from pathlib import Path

from .schemas import user, message
from .encryption.encryption import get_db_key

class Database: 
    def __init__(self) -> None:
        path = str(
            Path(__file__).parent.parent / "data" / "database.db"
        )
        self._conn = dbapi2.connect(path, isolation_level=None)
        self._conn.row_factory = dbapi2.Row
        self._conn.execute(f'''--sql
            PRAGMA key = '{get_db_key()}'
        ''')
    
    @contextmanager
    def transaction(self):
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            yield self._conn
        except BaseException:
            try:
                self._conn.execute("ROLLBACK")
            except Exception:
                pass
            raise
        else:
            self._conn.execute("COMMIT")

    def close(self) -> None:
        self._conn.close()

class UserRepo:
    def __init__(self, db: Database) -> None:
        self.db = db

    def create_user(self, usr: user.CreateUserPost, user_id: int) -> None:
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute('''--sql
                INSERT INTO users (user_id, user_name, hash)
                VALUES
                    (?, ?, ?)
                ''', 
                (user_id, usr.name, usr.hash)
            )

    def get_user_hash(self, id: int) -> str | None:
        with self.db.transaction() as conn: 
            cursor = conn.cursor()
            cursor.execute('''
                SELECT hash FROM users WHERE id = ?
                ''',
                (id, )
            )
            row = cursor.fetchone()
        return row["hash"] if row else None

    def get_accounts(self) -> user.Accounts | None:
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute('''--sql
                SELECT id, user_id, user_name, hash FROM users
            ''')
            row = cursor.fetchall()

        if not row:
            return None
        else:
            return user.Accounts(accounts=[dict(i) for i in row])

class ContactRepo:
    def __init__(self, db: Database, user_local_id: int) -> None:
        self.db = db
        self.user_local_id: int = user_local_id

    def add_contact(self, user_id: int, name: str) -> None:
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute('''--sql
                INSERT INTO contacts (master_id, user_id, name)
                VALUES
                    (?, ?, ?)
                ''',
                (self.user_local_id, user_id, name)
            )

    def get_contacts(self) -> user.Contacts | None:
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute('''--sql
                SELECT user_id, name FROM contacts 
                WHERE master_id = ?
                ''', 
                (self.user_local_id, )
            )
            row = cursor.fetchall()

        if not row: 
            return None
        else: 
            return user.Contacts(contacts=[dict(i) for i in row])

class MessageRepo:
    def __init__(self, db: Database, user_local_id: int) -> None:
        self.db = db
        self.user_local_id: int = user_local_id

    def add_received_messages(self, msg: message.MessagesGet) -> None:
        data = [
            (msg.sender_id, 
            self.user_local_id,
            msg.text, 
            msg.time, 
            msg.used_notepad) 
            for msg in msg.messages
        ]

        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.executemany('''--sql
                INSERT INTO messages (
                    sender_id, 
                    recipient_id,
                    text, 
                    time, 
                    used_notepad
                )
                VALUES
                    (?, ?, ?, ?, ?)
                ''',
                data
            )

    def add_sendet_message(self, msg: message.SendedMessage) -> None:
        data = [
            self.user_local_id, msg.recipient_id, msg.text, msg.time, msg.used_notepad, 1
        ]

        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute('''--sql
                INSERT INTO messages (
                    sender_id,
                    recipient_id, 
                    text, 
                    time, 
                    used_notepad, 
                    is_readed
                )
                VALUES
                    (?, ?, ?, ?, ?, ?)
                ''',
                data
            )

    # AI
    def get_history(self, peer_id: int) -> list[message.SendedMessage]:
        pass 

def init_db(db: Database) -> None: 
    with db.transaction() as conn:
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
                messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender_id INTEGER NOT NULL,
                    recipient_id INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    time INTEGER NOT NULL,
                    used_notepad INTEGER,
                    is_readed INTEGER DEFAULT 0 CHECK (is_readed IN (0, 1))
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