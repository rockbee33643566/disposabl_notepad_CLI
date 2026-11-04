import time

from . import utl
from . import database
from .api import API
from .schemas import user, message


class Client: 
    def __init__(self, api: API) -> None:
        self._api = api
        self._database = database
        self._user_local_id: int

    def set_user_local_id(self, id: int) -> None:
        self.user_local_id = id
        hash = self._database.get_user_hash(id)
        self._api.set_user_hash(hash)

    def create_user(self, name: str) -> None:
        usr = user.CreateUserPost(
            name=name, 
            hash=utl.generate_hash()
        )

        user_id = self._api.create_user(usr=usr)
        self._database.create_user(usr=usr, user_id=user_id)

    def is_user_exists(self, user_id) -> bool:
        return self._api.is_user_exists(id=user_id)

    def get_accounts(self) -> user.Accounts | None:
        return self._database.get_accounts()

    def send_message(
        self, text: str, user_local_id: int, recipient_id: int
    ) -> None:
        used_notepad = None
        user_hash = self._database.get_user_hash(id=user_local_id)
        msg_for_api = message.MessageSend(
            text=text, 
            sender_hash=user_hash, 
            recipient_id=recipient_id, 
            used_notepad=used_notepad
        )
        msg_for_db = message.SendedMessage(
            text=text, 
            recipient_id=recipient_id, 
            used_notepad=used_notepad,
            time=int(time.time())
        )

        self._api.send_message(msg=msg_for_api)
        self._database.add_sendet_message(msg=msg_for_db)

    def check_messages(self, user_local_id: int) -> message.MessagesGet | None:
        user_hash = self._database.get_user_hash(user_local_id)
        messages = self._api.check_messages(user_hash=user_hash)

        if not messages.messages: 
            return None

        cont = self.get_chats(user_local_id)
        if cont is None: 
            user_ids = []
        else: 
            user_ids = [i.user_id for i in cont.contacts]

        added_id = []

        for m in messages.messages: 
            if not m.sender_id in user_ids and not m.sender_id in added_id: 
                self.add_chat(user_local_id, m.sender_id, "Новый чат")
                added_id.append(m.sender_id)


        return messages

    def add_chat(self, user_local_id, contact_user_id: int, name: str) -> None: 
        self._database.add_contact(user_local_id, contact_user_id, name)

    def get_chats(self, user_local_id: int) -> user.Contacts | None: 
        return self._database.get_contact(user_local_id)
    