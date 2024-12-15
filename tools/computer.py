from .base import BaseAnthropicTool      
from typing import Dict, Any
from playwright.sync_api import Page
from anthropic.types.beta import BetaToolUnionParam
from typing_extensions import TypedDict
from typing import Literal
from core.claude import ClaudeManager
from playwright.sync_api import Browser, Page
from playwright.sync_api import sync_playwright
from enum import StrEnum
from tools.collection import ToolCollection
import os
import pyautogui
from anthropic.types.beta import BetaToolComputerUse20241022Param

OUTPUT_DIR = "/tmp/outputs"

TYPING_DELAY_MS = 12
TYPING_GROUP_SIZE = 50

Action = Literal[
    "key",
    "type",
    "mouse_move",
    "left_click",
    "left_click_drag",
    "right_click",
    "middle_click",
    "double_click",
    "screenshot",
    "cursor_position",
]

class Resolution(TypedDict):
    width: int
    height: int

class ComputerToolOptions(TypedDict):
    display_height_px: int
    display_width_px: int
    display_number: int | None

class ScalingSource(StrEnum):
    COMPUTER = "computer"
    API = "api"

# sizes above XGA/WXGA are not recommended (see README.md)
# scale down to one of these targets if ComputerTool._scaling_enabled is set
MAX_SCALING_TARGETS: dict[str, Resolution] = {
    "XGA": Resolution(width=1024, height=768),  # 4:3
    "WXGA": Resolution(width=1280, height=800),  # 16:10
    "FWXGA": Resolution(width=1366, height=768),  # ~16:9
}

class ComputerTool(BaseAnthropicTool):
    """
    A tool that allows the agent to interact with the screen, keyboard, and mouse of the current computer. 
    Hacked this a bit to use the browser and page objects from playwright.
    The tool parameters are defined by Anthropic and are not editable.
    """
    name: Literal["computer"] = "computer"
    api_type: Literal["computer_20241022"] = "computer_20241022"
    width: int
    height: int
    display_num: int | None

    _screenshot_delay = 2.0
    _scaling_enabled = True
    
    @property
    def options(self) -> ComputerToolOptions:
        width, height = self.scale_coordinates(
            ScalingSource.COMPUTER, self.width, self.height
        )
        return {
            "display_width_px": width,
            "display_height_px": height,
            "display_number": self.display_num,
        }
    
    async def __call__(
        self,
        *,
        action: Action,
        text: str | None = None,
        coordinate: tuple[int, int] | None = None,
        **kwargs,
    ):
        print("action", action)
        print("text", text)
        print("coordinate", coordinate)

    def to_params(self) -> BetaToolComputerUse20241022Param:
        return {"name": self.name, "type": self.api_type, **self.options}
    
    def __init__(self):
        super().__init__()
        print("Initializing ComputerTool")
        # self.browser = browser
        # self.page = page
        # get the width and hrigth of the whole screen from os
        self.width, self.height = pyautogui.size()
        # Validate dimensions
        assert self.width and self.height, "Browser viewport dimensions must be set"
        
        # Display settings (if needed)
        if (display_num := os.getenv("DISPLAY_NUM")) is not None:
            self.display_num = int(display_num)
            self._display_prefix = f"DISPLAY=:{self.display_num} "
        else:
            self.display_num = None
            self._display_prefix = ""
    
    def scale_coordinates(self, source: ScalingSource, x: int, y: int):
        """Scale coordinates to a target maximum resolution."""
        if not self._scaling_enabled:
            return x, y
        ratio = self.width / self.height
        target_dimension = None
        for dimension in MAX_SCALING_TARGETS.values():
            # allow some error in the aspect ratio - not ratios are exactly 16:9
            if abs(dimension["width"] / dimension["height"] - ratio) < 0.02:
                print("Target dimension found")
                if dimension["width"] < self.width:
                    print("Target dimension is less than screen width")
                    target_dimension = dimension
                break
        if target_dimension is None:
            return x, y
        # should be less than 1
        x_scaling_factor = target_dimension["width"] / self.width
        y_scaling_factor = target_dimension["height"] / self.height
        if source == ScalingSource.API:
            if x > self.width or y > self.height:
                raise ToolError(f"Coordinates {x}, {y} are out of bounds")
            # scale up
            return round(x / x_scaling_factor), round(y / y_scaling_factor)
        # scale down
        return round(x * x_scaling_factor), round(y * y_scaling_factor)
