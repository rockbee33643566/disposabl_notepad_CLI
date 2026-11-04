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

    def open_session(self, id: int) -> None:
        hash = self._users.get_user_hash(id)
        if hash is None:
            raise ValueError(f"Юзера с id - {id} не существует")
        api = UserAPI(self._api.base_url, self._api.http, hash)

        self._session = Session(self._db, api, id)

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

    def is_user_exists(self, user_id) -> bool:
        return self._api.is_user_exists(id=user_id)

    def get_accounts(self) -> user.Accounts | None:
        return self._users.get_accounts()

    def send_message(
        self, text: str, recipient_id: int
    ) -> None:
        used_notepad = None
        msg_for_db = message.SendedMessage(
            text=text, 
            recipient_id=recipient_id, 
            used_notepad=used_notepad,
            time=int(time.time())
        )

        self.session.api.send_message(
            text=text,
            recipient_id=recipient_id, 
            used_notepad=used_notepad
        )
        self.session.messages.add_sendet_message(msg=msg_for_db)

    def check_messages(self) -> message.MessagesGet | None:
        messages = self.session.api.check_messages()

        if not messages.messages: 
            return None

        cont = self.session.contacts.get_contacts()
        if cont is None: 
            user_ids = []
        else: 
            user_ids = [i.user_id for i in cont.contacts]

        added_id = []

        for m in messages.messages: 
            if not m.sender_id in user_ids and not m.sender_id in added_id: 
                self.add_chat(user_id=m.sender_id, name="Новый чат")
                added_id.append(m.sender_id)

        return messages

    def add_chat(self, user_id: int, name: str) -> None: 
        self.session.contacts.add_contact(user_id, name=name)

    def get_chats(self) -> user.Contacts | None: 
        return self.session.contacts.get_contacts()

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