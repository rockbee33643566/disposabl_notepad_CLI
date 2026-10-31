import utl 
import database
from api import API
from schemas import user, message


class Client: 
    def __init__(self, api: API) -> None:
        self.api = api

    def create_user(self, usr) -> None:
        user_id = self.api.create_user(usr=usr)
