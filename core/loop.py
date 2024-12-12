import os
from playwright.sync_api import sync_playwright
from typing import Dict, Any
import logging
from tools.computer import ComputerTool
from tools.navigation import NavigationTool
from tools.interaction import InteractionTool
from tools.extraction import ExtractionTool
from tools.javascript import JavaScriptTool
from core.claude import ClaudeManager
from core.sender import Sender


class ChatLoop:
    def __init__(self):
        """Initialize the chat loop with browser and tools"""
        self.browser = None
        self.page = None
        self.context = None
        self.playwright = None
        self.claude_manager = ClaudeManager()
        # Initialize tools
        self.tools = {
            'computer': ComputerTool(),
            'navigation': NavigationTool(),
            'interaction': InteractionTool(),
            'extraction': ExtractionTool(),
            'javascript': JavaScriptTool()
        }
        self.only_n_most_recent_images = 1 #keep default to 1
        
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
                no_viewport=True
            )
            self.page = self.context.new_page()
            logging.info("Browser initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize browser: {str(e)}")
            raise

    def get_response(self, conversation_history: list = None, render_callback=None, max_retries: int = 3) -> list:
        """Get response from Claude with message and handle tool interactions
        
        Args:
            conversation_history: List of previous messages
            render_callback: Optional callback to render messages
            max_retries: Maximum number of retries for Claude API calls
            
        Returns:
            List of messages including Claude's response and tool results
            
        Raises:
            Exception: If Claude API calls fail or tool processing fails
        """
        messages = conversation_history if conversation_history else []
        
        while True:
            try:
                # Get response from Claude
                try:
                    response = self.claude_manager.call_claude(conversation_history=messages, only_n_most_recent_images=self.only_n_most_recent_images)
                except Exception as e:
                    logging.error(f"Claude API call failed: {str(e)}")
                    raise Exception(f"Failed to get response from Claude after {max_retries} retries: {str(e)}")
                
                claude_message = {
                    "role": Sender.BOT,
                    "content": []
                }
                
                tool_results = []
                # Process each content block from Claude
                for content in response.content:
                    try:
                        if content.type == "text":
                            claude_message["content"].append({
                                "type": "text",
                                "text": content.text
                            })
                        elif content.type == "tool_use":
                            # Add tool use block
                            tool_block = {
                                "type": "tool_use",
                                "id": content.id,
                                "name": content.name,
                                "input": content.input
                            }
                            claude_message["content"].append(tool_block)
                            
                            # Process tool with error handling
                            try:
                                tool_result = self.process_tool_calls(content)
                                result_block = self.process_tool_output(tool_result, content.id)
                                claude_message["content"].append(result_block)
                                tool_results.append(result_block)
                            except Exception as e:
                                logging.error(f"Tool processing failed: {str(e)}")
                                error_block = {
                                    "type": "tool_result",
                                    "tool_use_id": content.id,
                                    "content": f"Tool execution failed: {str(e)}",
                                    "is_error": True
                                }
                                claude_message["content"].append(error_block)
                                tool_results.append(error_block)
                    except Exception as e:
                        logging.error(f"Failed to process content block: {str(e)}")
                        continue
                
                messages.append(claude_message)
                
                # Call render callback if provided
                if render_callback:
                    try:
                        render_callback(claude_message)
                    except Exception as e:
                        logging.error(f"Render callback failed: {str(e)}")
                
                # If no tools were used, we're done
                if not tool_results:
                    return messages
                    
                # Add tool results and continue loop
                tool_message = {
                    "role": Sender.USER,
                    "content": tool_results
                }
                messages.append(tool_message)
                
            except Exception as e:
                logging.error(f"Failed to get response: {str(e)}")
                raise Exception(f"Failed to get response: {str(e)}")
        
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