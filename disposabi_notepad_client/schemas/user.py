from pydantic import BaseModel

class CreateUserPost(BaseModel):
    name: str
    hash: str

class User(BaseModel):
    user_id: int
    user_name: str
    hash: str

class Users(BaseModel):
    users: list[User]

class Account(BaseModel):
    id: int
    user_id: int
    user_name: str

class Accounts(BaseModel):
    accounts: list[Account]