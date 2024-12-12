from .base import BaseAnthropicTool      
from typing import Dict, Any
from playwright.sync_api import Page
from anthropic.types.beta import BetaToolUnionParam

class ComputerTool(BaseAnthropicTool):
    def __call__(self, page: Page, command: str) -> Dict[str, Any]:
        pass

    def to_params(self) -> BetaToolUnionParam:
        return {"name": self.name, "type": self.api_type, **self.options}
