from pydantic import BaseModel
import typing as t

class ExternalToolSchema(BaseModel):
    """Schema definition for external tools."""
    name: str
    description: str
    input_schema: t.Dict[str, t.Any]
