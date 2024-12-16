from .base import BaseAnthropicTool
from typing import Dict, Any
from playwright.sync_api import Page
from anthropic.types.beta import BetaToolUnionParam

class BrowserTool():
    name = "BrowserTool"
    description = "Manages the playwright browser. This tool is used to navigate the web and extract information from the page."
    input_schema = {
        "type": "object",
        "properties": {
            "ticker": {
                "type": "string", 
                "description": "The stock ticker symbol, e.g. AAPL for Apple Inc."
            }
        },
        "required": ["ticker"]
    }
  
    def __call__(self, page: Page, command: str) -> Dict[str, Any]:
        pass

    def to_params(self) -> BetaToolUnionParam:
        return {"name": self.name, "description": self.description, "input_schema": self.input_schema}