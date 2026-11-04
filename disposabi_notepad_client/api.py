from requests import Session

from .schemas import user, message

class ClientApi:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.http = Session()

    def create_user(self, usr: user.CreateUserPost) -> int: 
        path = "/user/create"
        json = usr.model_dump()

        response = self.http.post(self.base_url + path, json=json)
        response.raise_for_status()

        data = response.json()

        return data

    def is_user_exists(self, id: int) -> bool:
        path = "/user/is_exists"
        params = {"id": id}

        response = self.http.get(
            url=self.base_url + path, 
            params=params
        )
        response.raise_for_status()

        data = response.json()

        return data

class UserAPI:
    def __init__(
            self, 
            base_url: str,  
            http: Session,
            user_hash: str):
        self.base_url = base_url
        self._user_hash = user_hash
        self.http = http

    def send_message(self, text: str, recipient_id: int, used_notepad: int | None) -> None:
        path = "/message/send"
        msg = message.MessageSend(
                    text=text, 
                    sender_hash=self._user_hash, 
                    recipient_id=recipient_id, 
                    used_notepad=used_notepad
                )
        json = msg.model_dump()

        response = self.http.post(
            url=self.base_url + path, 
            json=json
        )
        response.raise_for_status()

    def check_messages(self) -> message.MessagesGet: 
        path = "/message/get"
        params = {"user_hash": self._user_hash}

        response = self.http.get(
            url=self.base_url + path, 
            params=params
        )
        response.raise_for_status()

        data = response.json()

        return message.MessagesGet.model_validate(data)