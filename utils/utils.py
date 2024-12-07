import pyautogui
import os
from datetime import datetime

def take_screenshot():
    """
    Takes a screenshot of the current screen and saves it with a timestamp.
    Returns the path to the saved screenshot.
    """
    # Create screenshots directory if it doesn't exist
    screenshots_dir = "screenshots"
    if not os.path.exists(screenshots_dir):
        os.makedirs(screenshots_dir)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"screenshot_{timestamp}.png"
    filepath = os.path.join(screenshots_dir, filename)
    
    # Take and save screenshot
    screenshot = pyautogui.screenshot()
    screenshot.save(filepath)
    
    return filepath
