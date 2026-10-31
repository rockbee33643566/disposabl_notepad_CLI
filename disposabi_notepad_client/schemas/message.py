from pydantic import BaseModel

class Message(BaseModel):
    text: str
    recipient_id: int
    used_notepad: int
    time: int

class MessagesGet(BaseModel):
    messages: list[Message]

class MessageSend(BaseModel):
    text: str
    sender_hash: str
    recipient_id: int
    used_notepad: int