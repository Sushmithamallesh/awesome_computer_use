import os
import threading
from playwright.sync_api import sync_playwright
from typing import Dict, Any, Optional
import logging
from queue import Queue
from tools.computer import ComputerTool
from core.claude import ClaudeManager
from core.sender import Sender
from tools.collection import ToolCollection
from tools.browsertools import BrowserTool
from core.manager import BrowserManager
import streamlit as st

@st.cache_resource
def get_browser_manager():
    return BrowserManager(headless=False)

class ChatLoop:
    def __init__(self):
        """Initialize the chat loop with tools and browser manager."""
        self.claude_manager = ClaudeManager()
        self.only_n_most_recent_images = 1
        
        
        if not hasattr(st.session_state, 'browser_manager'):
            print("Creating new browser manager")
            st.session_state.browser_manager = BrowserManager()
        
        
        # Initialize browser manager first
        self.browser_manager = st.session_state.browser_manager
        
        # Initialize tools with browser manager
        self.tool_collection = ToolCollection(
            ComputerTool(browser_manager=self.browser_manager),
        )
    
    def _handle_tool_execution(self, content, messages, render_callback) -> tuple[dict, bool]:
        """Handle tool execution and create appropriate messages."""
        tool_block = {
            "type": "tool_use",
            "id": content.id,
            "name": content.name,
            "input": content.input
        }
        
        tool_result_message = {"role": Sender.USER, "content": []}
        
        try:
            tool_result = self.tool_collection.run(
                name=content.name,
                tool_input=content.input
            )
            result_block = self.tool_collection.process_tool_output(
                tool_result,
                content.id
            )
            tool_result_message["content"].append(result_block)
            return tool_result_message, True
            
        except Exception as e:
            error_block = {
                "type": "tool_result",
                "tool_use_id": content.id,
                "content": f"Tool execution failed: {str(e)}",
                "is_error": True
            }
            tool_result_message["content"].append(error_block)
            return tool_result_message, False

    def get_response(self, conversation_history: list = None, render_callback=None, max_retries: int = 1) -> list:
        """Get response from Claude and handle tool executions."""
        messages = conversation_history if conversation_history else []
        
        while True:
            try:
                # Get response from Claude
                response = self.claude_manager.call_claude(
                    conversation_history=messages,
                    only_n_most_recent_images=self.only_n_most_recent_images,
                    tool_collection=self.tool_collection
                )
                
                claude_message = {"role": Sender.ASSISSTANT, "content": []}
                tool_result_message = None
                continue_loop = False
                
                # Process each content block from Claude's response
                for content in response.content:
                    if content.type == "text":
                        claude_message["content"].append({
                            "type": "text",
                            "text": content.text
                        })
                    elif content.type == "tool_use":
                        claude_message["content"].append({
                            "type": "tool_use",
                            "id": content.id,
                            "name": content.name,
                            "input": content.input
                        })
                        
                        # Execute tool and get result
                        tool_result_message, should_continue = self._handle_tool_execution(
                            content, messages, render_callback
                        )
                        continue_loop = continue_loop or should_continue
                
                # Add Claude's message to history
                messages.append(claude_message)
                if render_callback:
                    render_callback(claude_message)
                
                # If no tool was used or tool execution failed, return messages
                if not tool_result_message:
                    return messages
                
                # Add tool result to history
                messages.append(tool_result_message)
                if render_callback:
                    render_callback(tool_result_message)
                
                # Continue loop if needed for additional tool actions
                if not continue_loop:
                    return messages
                
            except Exception as e:
                logging.error(f"Failed to get response: {str(e)}")
                # Clean up browser resources on error
                self.browser_manager.cleanup()
                raise
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        try:
            # Clean up browser resources
            self.browser_manager.cleanup()
        except Exception as e:
            logging.error(f"Error during cleanup: {str(e)}")
        messages = conversation_history if conversation_history else []
        
        while True:
            try:
                response = self.claude_manager.call_claude(
                    conversation_history=messages,
                    only_n_most_recent_images=self.only_n_most_recent_images,
                    tool_collection=self.tool_collection
                )
                
                claude_message = {"role": Sender.ASSISSTANT, "content": []}
                tool_result_message = None
                
                for content in response.content:
                    if content.type == "text":
                        claude_message["content"].append({
                            "type": "text",
                            "text": content.text
                        })
                    elif content.type == "tool_use":
                        tool_block = {
                            "type": "tool_use",
                            "id": content.id,
                            "name": content.name,
                            "input": content.input
                        }
                        claude_message["content"].append(tool_block)
                        
                        tool_result_message = {"role": Sender.USER, "content": []}
                        try:
                            tool_result = self.tool_collection.run(
                                name=content.name,
                                tool_input=content.input
                            )
                            result_block = self.tool_collection.process_tool_output(
                                tool_result,
                                content.id
                            )
                            tool_result_message["content"].append(result_block)
                        except Exception as e:
                            error_block = {
                                "type": "tool_result",
                                "tool_use_id": content.id,
                                "content": f"Tool execution failed: {str(e)}",
                                "is_error": True
                            }
                            tool_result_message["content"].append(error_block)
                
                messages.append(claude_message)
                if render_callback:
                    render_callback(claude_message)
                
                if not tool_result_message:
                    return messages
                    
                messages.append(tool_result_message)
                if render_callback:
                    render_callback(tool_result_message)
                
                print("claude_message", claude_message)
                
            except Exception as e:
                logging.error(f"Failed to get response: {str(e)}")
                raise