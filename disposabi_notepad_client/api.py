import requests

from .schemas import user, message

class API:
    def __init__(self, base_url: str):
        self.base_url = base_url

    def create_user(self, usr: user.CreateUserPost) -> int: 
        path = "/user/create"
        json = usr.model_dump()

        response = requests.post(self.base_url + path, json=json)
        response.raise_for_status()

        data = response.json()

        return data

    def is_user_exists(self, id: int) -> bool:
        path = "/user/is_exists"
        params = {"id": id}

        response = requests.get(
            url=self.base_url + path, 
            params=params
        )
        response.raise_for_status()

        data = response.json()

        return data

    def send_message(self, msg: message.MessageSend) -> None:
        path = "/message/send"
        json = msg.model_dump()

        response = requests.post(
            url=self.base_url + path, 
            json=json
        )
        response.raise_for_status()

    def check_messages(self, user_hash: str) -> message.MessagesGet: 
        path = "/message/get"
        params = {"user_hash": user_hash}

        response = requests.get(
            url=self.base_url + path, 
            params=params
        )
        response.raise_for_status()

        data = response.json()

        return message.MessagesGet.model_validate(data)