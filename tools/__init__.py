from abc import ABC, abstractmethod
from typing import Dict, Any
from playwright.sync_api import Page

class BaseTool(ABC):
    """Base class for all tools"""
    
    @abstractmethod
    def execute(self, page: Page, command: str) -> Dict[str, Any]:
        """
        Execute the tool's functionality
        
        Args:
            page (Page): Playwright page object
            command (str): Command to execute
            
        Returns:
            Dict[str, Any]: Result of the execution
        """
        pass
