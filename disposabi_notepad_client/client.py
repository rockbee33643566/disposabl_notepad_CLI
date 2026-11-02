import time

from . import utl
from . import database
from .api import API
from .schemas import user, message


class Client: 
    def __init__(self, api: API) -> None:
        self.api = api

    def create_user(self, name: str) -> None:
        usr = user.CreateUserPost(
            name=name, 
            hash=utl.generate_hash()
        )

        user_id = self.api.create_user(usr=usr)
        database.create_user(usr=usr, user_id=user_id)

    def is_user_exists(self, user_id) -> bool:
        return self.api.is_user_exists(id=user_id)

    def get_accounts(self) -> user.Accounts:
        return database.get_accounts()

    def send_message(
        self, text: str, user_local_id: int, recipient_id: int
    ) -> None:
        used_notepad = None
        user_hash = database.get_user_hash(id=user_local_id)
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

        self.api.send_message(msg=msg_for_api)
        database.add_sendet_message(msg=msg_for_db)

    def check_messages(self, user_local_id) -> message.MessagesGet:
        user_hash = database.get_user_hash(user_local_id)
        return self.api.check_messages(user_hash=user_hash)