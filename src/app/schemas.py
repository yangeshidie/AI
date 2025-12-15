from typing import List, Optional
from pydantic import BaseModel

class FileActionRequest(BaseModel):
    filename: str
    new_name: Optional[str] = None
    confirm_delete: bool = False

class HistoryActionRequest(BaseModel):
    filename: str
    new_name: Optional[str] = None

class LoadHistoryRequest(BaseModel):
    filepath: str

class ChatRequest(BaseModel):
    api_url: str
    api_key: str
    model: str
    messages: list
    session_file: str
    kb_id: Optional[str] = None

class CreateKBRequest(BaseModel):
    name: str
    description: str
    files: List[str]

class DeleteKBRequest(BaseModel):
    kb_id: str

class ModelListRequest(BaseModel):
    api_url: str
    api_key: str