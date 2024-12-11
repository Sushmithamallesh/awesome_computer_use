from enum import StrEnum

class Sender(StrEnum):
    USER = "user"
    BOT = "assistant"
    TOOL = "tool"
    