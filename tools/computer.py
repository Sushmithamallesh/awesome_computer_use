from typing import Dict, Any, Literal, Optional, Tuple
from typing_extensions import TypedDict
from enum import StrEnum
from anthropic.types.beta import BetaToolComputerUse20241022Param
from .base import BaseAnthropicTool, ToolResult, ToolError
from utils.utils import screenshot_helper
import os
TYPING_DELAY_MS = 12

class Action(StrEnum):
    KEY = "key"
    TYPE = "type"
    MOUSE_MOVE = "mouse_move"
    LEFT_CLICK = "left_click"
    LEFT_CLICK_DRAG = "left_click_drag"
    RIGHT_CLICK = "right_click"
    MIDDLE_CLICK = "middle_click"
    DOUBLE_CLICK = "double_click"
    SCREENSHOT = "screenshot"
    CURSOR_POSITION = "cursor_position"

class Resolution(TypedDict):
    width: int
    height: int

class ComputerToolOptions(TypedDict):
    display_height_px: int
    display_width_px: int
    display_number: Optional[int]

class ScalingSource(StrEnum):
    COMPUTER = "computer"
    API = "api"

MAX_SCALING_TARGETS: Dict[str, Resolution] = {
    "XGA": Resolution(width=1024, height=768),
    "WXGA": Resolution(width=1280, height=800),
    "FWXGA": Resolution(width=1366, height=768),
}

class ComputerTool(BaseAnthropicTool):
    name: Literal["computer"] = "computer"
    api_type: Literal["computer_20241022"] = "computer_20241022"
    
    def __init__(self, browser_manager: "BrowserManager"):
        """Initialize computer tool with browser manager."""
        super().__init__()
        self.browser_manager = browser_manager
        
        # Get viewport dimensions
        with self.browser_manager.get_page() as page:
            viewport = page.viewport_size
            self.width, self.height = viewport["width"], viewport["height"]
        
        assert self.width and self.height, "Browser viewport dimensions must be set"
        
        # Configuration
        self.display_num = int(os.getenv("DISPLAY_NUM", -1))
        self._screenshot_delay = 2.0
        self._scaling_enabled = True
    
    @property
    def options(self) -> ComputerToolOptions:
        """Get tool options with scaled dimensions."""
        width, height = self.scale_coordinates(
            ScalingSource.COMPUTER, 
            self.width, 
            self.height
        )
        return {
            "display_width_px": width,
            "display_height_px": height,
            "display_number": self.display_num if self.display_num >= 0 else None
        }
    
    def to_params(self) -> BetaToolComputerUse20241022Param:
        """Convert tool to API parameters."""
        return {"name": self.name, "type": self.api_type, **self.options}

    def scale_coordinates(self, source: ScalingSource, x: int, y: int) -> Tuple[int, int]:
        """Scale coordinates based on viewport and target dimensions."""
        if not self._scaling_enabled:
            return x, y
            
        ratio = self.width / self.height
        target_dimension = None
        
        # Find matching target dimension
        for dimension in MAX_SCALING_TARGETS.values():
            if abs(dimension["width"] / dimension["height"] - ratio) < 0.02:
                if dimension["width"] < self.width:
                    target_dimension = dimension
                break
        
        if target_dimension is None:
            return x, y
            
        # Calculate scaling factors
        x_scaling_factor = target_dimension["width"] / self.width
        y_scaling_factor = target_dimension["height"] / self.height
        
        if source == ScalingSource.API:
            if x > self.width or y > self.height:
                raise ToolError(f"Coordinates {x}, {y} are out of bounds")
            return round(x / x_scaling_factor), round(y / y_scaling_factor)
            
        return round(x * x_scaling_factor), round(y * y_scaling_factor)

    def __call__(self, *, action: Action, text: Optional[str] = None, 
                coordinate: Optional[Tuple[int, int]] = None, **kwargs) -> ToolResult:
        """Execute computer action."""
        # Validate action and parameters
        if action in (Action.MOUSE_MOVE, Action.LEFT_CLICK_DRAG):
            if coordinate is None:
                raise ToolError(f"coordinate is required for {action}")
            if text is not None:
                raise ToolError(f"text is not accepted for {action}")
            if not isinstance(coordinate, (list, tuple)) or len(coordinate) != 2:
                raise ToolError(f"{coordinate} must be a tuple of length 2")
            if not all(isinstance(i, int) and i >= 0 for i in coordinate):
                raise ToolError(f"{coordinate} must be a tuple of non-negative ints")

            x, y = self.scale_coordinates(ScalingSource.API, coordinate[0], coordinate[1])
            return (self.page_move_to_coordinates(x, y) if action == Action.MOUSE_MOVE 
                   else self.page_left_click_drag(x, y))

        if action in (Action.KEY, Action.TYPE):
            if text is None:
                raise ToolError(f"text is required for {action}")
            if coordinate is not None:
                raise ToolError(f"coordinate is not accepted for {action}")
            if not isinstance(text, str):
                raise ToolError(f"{text} must be a string")

            return self.page_key(text) if action == Action.KEY else self.page_type(text)

        if action in (Action.LEFT_CLICK, Action.RIGHT_CLICK, Action.MIDDLE_CLICK, 
                     Action.DOUBLE_CLICK, Action.SCREENSHOT, Action.CURSOR_POSITION):
            if text is not None or coordinate is not None:
                raise ToolError(f"No parameters accepted for {action}")

            if action == Action.SCREENSHOT:
                return self.screenshot()
            if action == Action.CURSOR_POSITION:
                return self.page_cursor_position()
            return self.page_click(action)

        raise ToolError(f"Invalid action: {action}")

    def screenshot(self) -> ToolResult:
        """Take a screenshot of the current page."""
        try:
            with self.browser_manager.get_page() as page:
                screenshot_base64 = screenshot_helper(page)
                return ToolResult(
                    output="Screenshot taken",
                    base64_image=screenshot_base64
                )
        except Exception as e:
            return ToolResult(error=f"Failed to take screenshot: {str(e)}")

    def page_move_to_coordinates(self, x: int, y: int, take_screenshot: bool = True) -> ToolResult:
        """Move mouse to specified coordinates."""
        try:
            with self.browser_manager.get_page() as page:
                page.mouse.move(x, y)
                result = f"Moved mouse to coordinates x={x}, y={y}"
                
                if take_screenshot:
                    screenshot_base64 = screenshot_helper(page)
                    return ToolResult(output=result, base64_image=screenshot_base64)
                return ToolResult(output=result)
        except Exception as e:
            return ToolResult(error=f"Failed to move mouse: {str(e)}")

    def page_left_click_drag(self, x: int, y: int, take_screenshot: bool = True) -> ToolResult:
        """Perform click and drag operation."""
        try:
            with self.browser_manager.get_page() as page:
                start_pos = page.mouse.position
                page.mouse.down()
                page.mouse.move(x, y)
                page.mouse.up()
                
                result = f"Dragged from {start_pos} to ({x}, {y})"
                
                if take_screenshot:
                    screenshot_base64 = screenshot_helper(page)
                    return ToolResult(output=result, base64_image=screenshot_base64)
                return ToolResult(output=result)
        except Exception as e:
            return ToolResult(error=f"Failed to drag: {str(e)}")

    def page_key(self, key: str, take_screenshot: bool = True) -> ToolResult:
        """Press a keyboard key."""
        try:
            with self.browser_manager.get_page() as page:
                page.keyboard.press(key)
                
                if take_screenshot:
                    screenshot_base64 = screenshot_helper(page)
                    return ToolResult(output=f"Pressed key: {key}", base64_image=screenshot_base64)
                return ToolResult(output=f"Pressed key: {key}")
        except Exception as e:
            return ToolResult(error=f"Failed to press key: {str(e)}")

    def page_type(self, text: str, take_screenshot: bool = True) -> ToolResult:
        """Type text with delay between keystrokes."""
        try:
            with self.browser_manager.get_page() as page:
                page.keyboard.type(text, delay=TYPING_DELAY_MS)
                
                if take_screenshot:
                    screenshot_base64 = screenshot_helper(page)
                    return ToolResult(output=f"Typed text: {text}", base64_image=screenshot_base64)
                return ToolResult(output=f"Typed text: {text}")
        except Exception as e:
            return ToolResult(error=f"Failed to type text: {str(e)}")

    def page_click(self, action: Action, take_screenshot: bool = True) -> ToolResult:
        """Perform various click actions."""
        try:
            with self.browser_manager.get_page() as page:
                pos = page.mouse.position
                
                if action == Action.LEFT_CLICK:
                    page.mouse.click(pos[0], pos[1])
                elif action == Action.RIGHT_CLICK:
                    page.mouse.click(pos[0], pos[1], button='right')
                elif action == Action.MIDDLE_CLICK:
                    page.mouse.click(pos[0], pos[1], button='middle')
                elif action == Action.DOUBLE_CLICK:
                    page.mouse.dblclick(pos[0], pos[1])
                
                if take_screenshot:
                    screenshot_base64 = screenshot_helper(page)
                    return ToolResult(output=f"Performed {action} at {pos}", base64_image=screenshot_base64)
                return ToolResult(output=f"Performed {action} at {pos}")
        except Exception as e:
            return ToolResult(error=f"Failed to perform {action}: {str(e)}")

    def page_cursor_position(self) -> ToolResult:
        """Get current cursor position."""
        try:
            with self.browser_manager.get_page() as page:
                pos = page.mouse.position
                return ToolResult(output=f"Cursor position: x={pos[0]}, y={pos[1]}")
        except Exception as e:
            return ToolResult(error=f"Failed to get cursor position: {str(e)}")