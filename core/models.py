from enum import StrEnum
from typing import Optional, Union
from pydantic import BaseModel

class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"

class UIMessage(BaseModel):
    """Lightweight message type for UI display"""
    role: MessageRole
    content: str
    screenshot: Optional[str] = None
    tool_output: Optional[str] = None
    error: Optional[str] = None




