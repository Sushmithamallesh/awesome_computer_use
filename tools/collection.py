"""Collection classes for managing multiple tools."""

from typing import Any

from anthropic.types.beta import BetaToolUnionParam

from .base import (
    BaseAnthropicTool,
    ToolError,
    ToolFailure,
    ToolResult,
)

class ToolCollection:
    """A collection of anthropic-defined tools."""

    def __init__(self, *tools: BaseAnthropicTool):
        self.tools = tools
        self.tool_map = {tool.to_params()["name"]: tool for tool in tools}

    def to_params(
        self,
    ) -> list[BetaToolUnionParam]:
        return [tool.to_params() for tool in self.tools]
    
    def run(self, *, name: str, tool_input: dict[str, Any]) -> ToolResult:
        tool = self.tool_map.get(name)
        if not tool:
            return ToolFailure(error=f"Tool {name} is invalid")
        try:
            return tool(**tool_input)
        except ToolError as e:
            return ToolFailure(error=e.message)
    
    def process_tool_output(self, tool_result: ToolResult, tool_use_id: str) -> dict:
        tool_result_content = []
        is_error = bool(tool_result.error)

        if tool_result.error    :
            tool_result_content.append({
                "type": "text",
                "text": tool_result.error
            })
        elif tool_result.output:
            tool_result_content.append({
                "type": "text",
                "text": tool_result.output
            })
        
        if tool_result.base64_image:
            tool_result_content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": tool_result.base64_image
                }
            })

        return {
            "type": "tool_result",
            "content": tool_result_content,
            "tool_use_id": tool_use_id,
            "is_error": is_error
        }