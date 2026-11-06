import asyncio
import time
from collections.abc import Awaitable, Callable

from . import utl, logger
from .database import Database, MessageRepo, ContactRepo, UserRepo
from .api import ClientApi, UserAPI
from .schemas import user, message

POLLING_INTERVAL = 1.0


class Client: 
    def __init__(
            self, 
            client_api: ClientApi,
            database: Database, 
            user_repo: UserRepo
        ) -> None:
        self._db = database
        self._api = client_api
        self._users = user_repo
        self._log = logger.get_logger()
        self._session: Session | None = None
        self._polling_task: asyncio.Task | None = None

    async def open_session(self, local_id: int) -> None:
        await self.stop_long_polling()

        hash = await self._users.get_user_hash(local_id)
        if hash is None:
            await self._log.warning(f"Попытка входа в несуществующий аккаунт id={local_id}")
            raise ValueError(f"Юзера с id - {local_id} не существует")
        api = UserAPI(self._api.base_url, self._api.http, hash)

        self._session = Session(self._db, api, local_id)
        await self._log.info(f"Сессия открыта для аккаунта id={local_id}")

    @property
    def session(self) -> Session:
        if self._session is None: 
            raise RuntimeError("Сессия не открыта. Используйте метод open_session(id) для открытия сессии")
        return self._session

    async def create_user(self, name: str) -> None:
        usr = user.CreateUserPost(
            name=name, 
            hash=utl.generate_hash()
        )

        user_id = await self._api.create_user(usr=usr)
        await self._users.create_user(usr=usr, user_id=user_id)
        await self._log.info(f"Создан аккаунт name={name!r} id={user_id}")

    async def is_user_exists(self, user_id: int) -> bool:
        return await self._api.is_user_exists(id=user_id)

    async def get_accounts(self) -> user.Accounts | None:
        return await self._users.get_accounts()

    async def send_message(
        self, text: str, recipient_id: int
    ) -> None:
        await self.session.api.send_message(
            text=text,
            recipient_id=recipient_id, 
            used_notepad=None
        )
        await self.session.messages.add_sendet_message(
            message.SendedMessage(
                text=text,
                recipient_id=recipient_id,
                used_notepad=None,
                time=int(time.time())
            )
        )
        await self._log.info(
            f"Сообщение отправлено получателю id={recipient_id}, длина={len(text)}"
        )

    async def check_messages(self) -> list[message.Message]:
        result = await self.session.api.check_messages()
        if result.messages:
            await self.session.messages.add_received_messages(result.messages)
            await self._log.info(f"Получено сообщений: {len(result.messages)}")
        return result.messages

    async def get_chats(self) -> list[dict]:
        return await self.session.messages.get_chats()

    async def get_chat_history(self, peer_id: int) -> list[message.HistoryMessage]:
        return await self.session.messages.get_history(peer_id)

    async def set_long_polling_callback(
        self, call_back: Callable[[list[message.Message]], Awaitable[None]]
    ) -> None:
        await self.stop_long_polling()
        self._polling_task = asyncio.create_task(self._polling_loop(call_back))

    async def _polling_loop(
        self, call_back: Callable[[list[message.Message]], Awaitable[None]]
    ) -> None:
        await self._log.info("Длинный полинг запущен")
        while True:
            try:
                messages = await self.check_messages()
                if messages:
                    await call_back(messages)
            except Exception as exc:
                await self._log.exception(f"Ошибка длинного полинга: {exc}")
            await asyncio.sleep(POLLING_INTERVAL)

    async def stop_long_polling(self) -> None:
        if self._polling_task is None:
            return

        self._polling_task.cancel()
        try:
            await self._polling_task
        except asyncio.CancelledError:
            pass
        self._polling_task = None
        await self._log.info("Длинный полинг остановлен")


class Session: 
    def __init__(
            self, 
            db: Database, 
            api: UserAPI,
            user_local_id: int
        ) -> None:
        self.db = db
        self.contacts = ContactRepo(db, user_local_id)
        self.messages = MessageRepo(db, user_local_id)
        self.api = api

        self.user_local_id: int = user_local_id
