import os
from playwright.sync_api import sync_playwright
from typing import Dict, Any
import logging
from tools.computer import ComputerTool
from core.claude import ClaudeManager
from core.sender import Sender
from tools.collection import ToolCollection

class ChatLoop:
    def __init__(self):
        """Initialize the chat loop with browser and tools"""
        self.browser = None
        self.page = None
        self.context = None
        self.playwright = None
        self.claude_manager = ClaudeManager()
        # Initialize tools
        self.only_n_most_recent_images = 1 #keep default to 1
        
        # Start browser session
        self._initialize_browser()
        
        print("Browser initialized successfully")
        print("page", self.page)
        
        # Initialize tools
        self.tool_collection = ToolCollection(
            ComputerTool()
        )

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
        except Exception as e:
            logging.error(f"Failed to initialize browser: {str(e)}")
            raise

    def get_response(self, conversation_history: list = None, render_callback=None, max_retries: int = 1) -> list:
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
                    response = self.claude_manager.call_claude(
                        conversation_history=messages, 
                        only_n_most_recent_images=self.only_n_most_recent_images, 
                        tool_collection=self.tool_collection
                    )
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
        

    def __del__(self):
        """Cleanup browser resources"""
        try:
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
        except Exception as e:
            logging.error(f"Error during cleanup: {str(e)}") 