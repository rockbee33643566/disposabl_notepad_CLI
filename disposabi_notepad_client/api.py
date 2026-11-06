from aiohttp import ClientSession

import asyncio

from .schemas import user, message

class ClientApi:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.http = ClientSession()

    async def create_user(self, usr: user.CreateUserPost) -> int: 
        path = "/user/create"
        json = usr.model_dump()

        async with self.http.post(
            url=self.base_url + path, json=json
        ) as response:
            response.raise_for_status()

            data = await response.json()

        return data

    async def is_user_exists(self, id: int) -> bool:
        path = "/user/is_exists"
        params = {"id": id}

        async with self.http.get(
            url=self.base_url + path, 
            params=params
        ) as response:
            response.raise_for_status()

            data = await response.json()

        return data

class UserAPI:
    def __init__(
            self, 
            base_url: str,  
            http: ClientSession,
            user_hash: str):
        self.base_url = base_url
        self._user_hash = user_hash
        self.http = http

    async def send_message(self, text: str, recipient_id: int, used_notepad: int | None) -> None:
        path = "/message/send"
        msg = message.MessageSend(
                    text=text, 
                    sender_hash=self._user_hash, 
                    recipient_id=recipient_id, 
                    used_notepad=used_notepad
                )
        json = msg.model_dump()

        async with self.http.post(
            url=self.base_url + path, 
            json=json
        ) as response:
            response.raise_for_status()

    async def check_messages(self) -> message.MessagesGet: 
        path = "/message/get"
        params = {"user_hash": self._user_hash}

        async with self.http.get(
            url=self.base_url + path, 
            params=params
        ) as response:
            response.raise_for_status()

            data = await response.json()

        return message.MessagesGet.model_validate(data)