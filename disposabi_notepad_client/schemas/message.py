from pydantic import BaseModel

class Message(BaseModel):
    text: str
    sender_id: int
    used_notepad: int | None
    time: int

class MessagesGet(BaseModel):
    messages: list[Message]

class MessageSend(BaseModel):
    text: str
    sender_hash: str
    recipient_id: int
    used_notepad: int | None

class SendedMessage(BaseModel): 
    text: str 
    recipient_id: int 
    used_notepad: int | None
    time: int