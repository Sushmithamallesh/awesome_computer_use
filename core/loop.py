import os
from playwright.sync_api import sync_playwright
from typing import Dict, Any
import logging
from tools.computer import ComputerTool
from tools.navigation import NavigationTool
from tools.interaction import InteractionTool
from tools.extraction import ExtractionTool
from tools.javascript import JavaScriptTool

class ChatLoop:
    def __init__(self):
        """Initialize the chat loop with browser and tools"""
        self.browser = None
        self.page = None
        self.context = None
        self.playwright = None
        
        # Initialize tools
        self.tools = {
            'computer': ComputerTool(),
            'navigation': NavigationTool(),
            'interaction': InteractionTool(),
            'extraction': ExtractionTool(),
            'javascript': JavaScriptTool()
        }
        
        # Start browser session
        self._initialize_browser()

    def _initialize_browser(self):
        """Initialize the browser session"""
        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(
                headless=False,  # Set to True if you don't want to see the browser
                args=['--start-maximized']
            )
            self.context = self.browser.new_context(
                viewport={'width': 1920, 'height': 1080}
            )
            self.page = self.context.new_page()
            logging.info("Browser initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize browser: {str(e)}")
            raise

    def process_message(self, message: str) -> Dict[str, Any]:
        """
        Process incoming messages and return appropriate responses
        
        Args:
            message (str): The user's input message
            
        Returns:
            Dict[str, Any]: Response containing message and optional screenshot
        """
        try:
            # Basic response structure
            response = {
                "message": "",
                "status": "success"
            }

            # Process the message and determine which tool to use
            if "navigate" in message.lower() or "go to" in message.lower():
                result = self.tools['navigation'].execute(self.page, message)
            elif "click" in message.lower() or "type" in message.lower():
                result = self.tools['interaction'].execute(self.page, message)
            elif "extract" in message.lower() or "get" in message.lower():
                result = self.tools['extraction'].execute(self.page, message)
            elif "script" in message.lower() or "javascript" in message.lower():
                result = self.tools['javascript'].execute(self.page, message)
            else:
                # Default to computer tool for general commands
                result = self.tools['computer'].execute(self.page, message)

            # Take screenshot after action
            screenshot_path = self._take_screenshot()
            if screenshot_path:
                response["screenshot"] = screenshot_path

            # Add tool execution result to response
            response["message"] = result.get("message", "Action completed successfully")
            
            return response

        except Exception as e:
            logging.error(f"Error processing message: {str(e)}")
            return {
                "message": f"An error occurred: {str(e)}",
                "status": "error"
            }

    def _take_screenshot(self) -> str:
        """
        Take a screenshot of the current page state
        
        Returns:
            str: Path to the screenshot file
        """
        try:
            # Create screenshots directory if it doesn't exist
            os.makedirs("screenshots", exist_ok=True)
            
            # Generate unique filename
            screenshot_path = f"screenshots/screenshot_{len(os.listdir('screenshots'))}.png"
            
            # Take screenshot
            self.page.screenshot(path=screenshot_path)
            return screenshot_path
        except Exception as e:
            logging.error(f"Failed to take screenshot: {str(e)}")
            return ""

    def __del__(self):
        """Cleanup browser resources"""
        try:
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
        except Exception as e:
            logging.error(f"Error during cleanup: {str(e)}") 