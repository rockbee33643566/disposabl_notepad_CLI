import sqlcipher3

import sys

sys.modules["sqlite3"] = sqlcipher3
import aiosqlite

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from pathlib import Path

from . import logger
from .schemas import user, message
from .encryption.encryption import get_db_key

class Database:
    def __init__(self) -> None:
        path = str(Path(__file__).parent.parent / "data" / "database.db")
        self._path = path
        self._conn: aiosqlite.Connection | None = None
        self._init_lock = asyncio.Lock()
        self._tx_lock = asyncio.Lock()
        self._log = logger.get_logger()

    async def _ensure_initialized(self) -> aiosqlite.Connection:
        if self._conn is not None:
            return self._conn

        async with self._init_lock:
            if self._conn is not None:
                return self._conn

            conn = await aiosqlite.connect(
                self._path,
                isolation_level=None,
                check_same_thread=False,
            )
            conn.row_factory = sqlcipher3.dbapi2.Row
            await conn.execute(f"PRAGMA key = '{get_db_key()}'")
            await conn.execute("PRAGMA busy_timeout = 5000")
            await conn.execute("PRAGMA journal_mode = WAL")
            self._conn = conn
            await self._log.info(f"Подключение к базе данных открыто: {self._path}")
            return conn

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[aiosqlite.Connection, None]:
        conn = await self._ensure_initialized()

        async with self._tx_lock:
            await conn.execute("BEGIN IMMEDIATE")
            try:
                yield conn
            except BaseException:
                await conn.execute("ROLLBACK")
                raise
            else:
                await conn.execute("COMMIT")

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.close()
            self._conn = None
            await self._log.info("Подключение к базе данных закрыто")

class UserRepo:
    def __init__(self, db: Database) -> None:
        self.db = db
        self._log = logger.get_logger()

    async def create_user(self, usr: user.CreateUserPost, user_id: int) -> None:
        async with self.db.transaction() as conn:
            await conn.execute('''--sql
                INSERT INTO users (user_id, user_name, hash)
                VALUES
                    (?, ?, ?)
                ''', 
                (user_id, usr.name, usr.hash)
            )
        await self._log.info(f"Пользователь сохранён в локальную базу id={user_id}")

    async def get_user_hash(self, id: int) -> str | None:
        async with self.db.transaction() as conn: 
            cursor = await conn.cursor()
            await cursor.execute('''
                SELECT hash FROM users WHERE id = ?
                ''',
                (id, )
            )
            row = await cursor.fetchone()
        return row["hash"] if row else None

    async def get_accounts(self) -> user.Accounts | None:
        async with self.db.transaction() as conn:
            cursor = await conn.cursor()
            await cursor.execute('''--sql
                SELECT id, user_id, user_name, hash FROM users
            ''')
            rows = await cursor.fetchall()

        if not rows:
            return None
        else:
            return user.Accounts(accounts=[dict(i) for i in rows])

class ContactRepo:
    def __init__(self, db: Database, user_local_id: int) -> None:
        self.db = db
        self.user_local_id: int = user_local_id
        self._log = logger.get_logger()

    async def add_contact(self, user_id: int, name: str) -> None:
        async with self.db.transaction() as conn:
            await conn.execute('''--sql
                INSERT INTO contacts (master_id, user_id, name)
                VALUES
                    (?, ?, ?)
                ''',
                (self.user_local_id, user_id, name)
            )
        await self._log.info(f"Контакт добавлен user_id={user_id} name={name!r}")

    async def get_contacts(self) -> user.Contacts | None:
        with self.db.transaction() as conn:
            cursor = await conn.cursor()
            await cursor.execute('''--sql
                SELECT user_id, name FROM contacts 
                WHERE master_id = ?
                ''', 
                (self.user_local_id, )
            )
            rows = await cursor.fetchall()

        if not rows: 
            return None
        else: 
            return user.Contacts(contacts=[dict(i) for i in rows])

class MessageRepo:
    def __init__(self, db: Database, user_local_id: int) -> None:
        self.db = db
        self.user_local_id: int = user_local_id
        self._log = logger.get_logger()

    async def add_received_messages(self, msgs: list[message.Message]) -> None:
        data = [
            (m.sender_id,
            self.user_local_id,
            m.text,
            m.time,
            m.used_notepad)
            for m in msgs
        ]

        async with self.db.transaction() as conn:
            await conn.executemany('''--sql
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
        await self._log.info(f"Входящих сообщений сохранено в базу: {len(data)}")

    async def add_sendet_message(self, msg: message.SendedMessage) -> None:
        data = [
            self.user_local_id, msg.recipient_id, msg.text, msg.time, msg.used_notepad, 1
        ]

        async with self.db.transaction() as conn:
            await conn.execute('''--sql
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
        await self._log.info(f"Исходящее сообщение сохранено в базу получателю id={msg.recipient_id}")

    async def get_history(self, peer_id: int) -> list[message.HistoryMessage]:
        async with self.db.transaction() as conn:
            cursor = await conn.cursor()
            await cursor.execute('''--sql
                SELECT
                    sender_id,
                    recipient_id,
                    text,
                    time,
                    used_notepad,
                    MAX(is_readed) AS is_readed
                FROM messages
                WHERE (sender_id = ? AND recipient_id = ?)
                   OR (sender_id = ? AND recipient_id = ?)
                GROUP BY sender_id, recipient_id, text, time, used_notepad
                ORDER BY time ASC, MIN(id) ASC
                ''',
                (self.user_local_id, peer_id, peer_id, self.user_local_id)
            )
            rows = await cursor.fetchall()

        return [message.HistoryMessage(**dict(r)) for r in rows]

    async def get_chats(self) -> list[dict]:
        async with self.db.transaction() as conn:
            cursor = await conn.cursor()
            await cursor.execute('''--sql
                SELECT peer_id, MAX(time) AS last_time
                FROM (
                    SELECT recipient_id AS peer_id, time FROM messages
                    WHERE sender_id = ?
                    UNION ALL
                    SELECT sender_id AS peer_id, time FROM messages
                    WHERE recipient_id = ?
                )
                GROUP BY peer_id
                ORDER BY last_time DESC
                ''',
                (self.user_local_id, self.user_local_id)
            )
            rows = await cursor.fetchall()

        async with asyncio.TaskGroup() as tg:
            tasks = tuple(
                tg.create_task(coro=self._create_chat(row)) for row in rows
            )

        chats = await asyncio.gather(*tasks)

        return chats

    async def _create_chat(self, row) -> dict: 
        peer_id = row["peer_id"]
        last = await self._last_message(peer_id)
        return {
            "peer_id": peer_id,
            "last_text": last["text"] if last else "",
            "last_time": row["last_time"],
        }

    async def _last_message(self, peer_id: int) -> dict | None:
        async with self.db.transaction() as conn:
            cursor = await conn.cursor()
            cursor.execute('''--sql
                SELECT text FROM messages
                WHERE (sender_id = ? AND recipient_id = ?)
                   OR (sender_id = ? AND recipient_id = ?)
                ORDER BY time DESC, id DESC
                LIMIT 1
                ''',
                (self.user_local_id, peer_id, peer_id, self.user_local_id)
            )
            row = await cursor.fetchone()
        return dict(row) if row else None

async def init_db(db: Database) -> None: 
    async with db.transaction() as conn:
        await conn.execute('''--sql
            CREATE TABLE IF NOT EXISTS 
                users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL UNIQUE, 
                    user_name TEXT, 
                    hash TEXT UNIQUE
                )
        ''')

        await conn.execute('''--sql
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

        await conn.execute('''--sql
            CREATE TABLE IF NOT EXISTS
                contacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    master_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL, 
                    name TEXT
                )
        ''')
    await logger.get_logger().info("Схема базы данных инициализирована")