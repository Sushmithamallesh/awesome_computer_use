def to_claude_request_type(messages: list[UIMessage]) -> list[Message]:
    """Convert UI messages to Claude request type"""
    return [Message(role=message.role, content=message.content) for message in messages]