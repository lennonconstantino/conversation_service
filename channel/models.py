from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum

class RoleType(str, Enum):
    ADMIN: str = "admin"
    BASIC: str = "basic"

class User(BaseModel):
    id: int
    first_name: str
    last_name: str
    role: RoleType = RoleType.BASIC

class Text(BaseModel):
    body: str

class Image(BaseModel):
    mime_type: str
    sha256: str
    id: str

class Audio(BaseModel):
    mime_type: str
    sha256: str
    id: str
    voice: bool

class Message(BaseModel):
    from_: str = Field(..., alias="from")
    id: str
    timestamp: str
    text: Optional[Text] = None
    image: Optional[Image] = None
    audio: Optional[Audio] = None
    type: str

class Value(BaseModel):
    messaging_product: str
    messages: Optional[List[Message]] = None

class Change(BaseModel):
    value: Value
    field: str

class Entry(BaseModel):
    id: str
    changes: List[Change]

class Payload(BaseModel):
    object: str
    entry: List[Entry]