import time

from . import utl
from .database import Database, MessageRepo, ContactRepo, UserRepo
from .api import ClientApi, UserAPI
from .schemas import user, message


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
        self._session: Session | None = None

    def open_session(self, local_id: int) -> None:
        hash = self._users.get_user_hash(local_id)
        if hash is None:
            raise ValueError(f"Юзера с id - {local_id} не существует")
        api = UserAPI(self._api.base_url, self._api.http, hash)

        self._session = Session(self._db, api, local_id)

    @property
    def session(self) -> Session:
        if self._session is None: 
            raise RuntimeError("Сессия не открыта. Используйте метод open_session(id) для открытия сессии")
        return self._session

    def create_user(self, name: str) -> None:
        usr = user.CreateUserPost(
            name=name, 
            hash=utl.generate_hash()
        )

        user_id = self._api.create_user(usr=usr)
        self._users.create_user(usr=usr, user_id=user_id)

    def is_user_exists(self, user_id: int) -> bool:
        return self._api.is_user_exists(id=user_id)

    def get_accounts(self) -> user.Accounts | None:
        return self._users.get_accounts()

    def send_message(
        self, text: str, recipient_id: int
    ) -> None:
        self.session.api.send_message(
            text=text,
            recipient_id=recipient_id, 
            used_notepad=None
        )
        self.session.messages.add_sendet_message(
            message.SendedMessage(
                text=text,
                recipient_id=recipient_id,
                used_notepad=None,
                time=int(time.time())
            )
        )

    def check_messages(self) -> list[message.Message]:
        result = self.session.api.check_messages()
        if result.messages:
            self.session.messages.add_received_messages(result.messages)
        return result.messages

    def get_chats(self) -> list[dict]:
        return self.session.messages.get_chats()

    def get_chat_history(self, peer_id: int) -> list[message.HistoryMessage]:
        return self.session.messages.get_history(peer_id)


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
