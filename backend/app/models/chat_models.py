from typing import List, Optional
from fastapi import UploadFile
from pydantic import BaseModel

class ChatRequest(BaseModel):
    query: str
    isSearchMode: bool
    session_id: Optional[int] = None  # Changed from chat_session_id

class ChatResponse(BaseModel): # Adjust if needed, SSE streaming changes this
    answer: str
    search: str
    duration: float

class PDFUpload(BaseModel):
    file: UploadFile