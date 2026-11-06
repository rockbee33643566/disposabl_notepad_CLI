from aiohttp import ClientSession

import asyncio

from . import logger
from .schemas import user, message

class ClientApi:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.http = ClientSession()
        self._log = logger.get_logger()

    async def create_user(self, usr: user.CreateUserPost) -> int: 
        path = "/user/create"
        json = usr.model_dump()

        async with self.http.post(
            url=self.base_url + path, json=json
        ) as response:
            response.raise_for_status()

            data = await response.json()

        await self._log.info(f"Аккаунт создан на сервере name={usr.name!r} id={data}")
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

        await self._log.info(f"Проверка существования пользователя id={id}: {data}")
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
        self._log = logger.get_logger()

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

        await self._log.info(f"Запрос на отправку сообщения получателю id={recipient_id} выполнен")

    async def check_messages(self) -> message.MessagesGet: 
        path = "/message/get"
        params = {"user_hash": self._user_hash}

        async with self.http.get(
            url=self.base_url + path, 
            params=params
        ) as response:
            response.raise_for_status()

            data = await response.json()

        result = message.MessagesGet.model_validate(data)
        await self._log.info(f"Запрос новых сообщений выполнен, получено={len(result.messages)}")
        return result