import pyautogui
import os
from datetime import datetime
from playwright.sync_api import Page
import base64
    
def screenshot_helper(page: Page) -> str:
    """
    Take a screenshot and return it as a base64 string.
    
    Args:
        page: Playwright Page object
    
    Returns:
        str: Base64 encoded screenshot
    """
    try:
        # Take screenshot as bytes with png format
        screenshot_bytes = page.screenshot(type="png")
        # Convert bytes to base64 string
        base64_string = base64.b64encode(screenshot_bytes).decode('utf-8')
        print("screnshot taken")
        
        return base64_string
    except Exception as e:
        print(f"Failed to take screenshot: {str(e)}")
        raise