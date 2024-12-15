from anthropic import Anthropic
from typing import Dict, Any
import os
from datetime import datetime
from utils.utils import take_screenshot
from anthropic.types.beta import (
    BetaContentBlockParam,
    BetaTextBlockParam,
    BetaToolUseBlockParam,
    BetaToolResultBlockParam,
)
from enum import StrEnum
import time
from typing import List
from tools.collection import ToolCollection
COMPUTER_USE_BETA_FLAG = "computer-use-2024-10-22"

# This system prompt is optimized for the Docker environment in this repository and
# specific tool combinations enabled.
# We encourage modifying this system prompt to ensure the model has context for the
# environment it is running in, and to provide any additional information that may be
# helpful for the task at hand.
SYSTEM_PROMPT = f"""<SYSTEM_CAPABILITY>
* You are utilizing a Mac with internet access. 
* I will open a Playwright instance for you to control. Please use this for all your browser needs and not pop open a new browser window. This is to make sure that you can use custom browser tools and be an expert at navigating the web.
* You can install Mac applications using brew. For downloading files, use curl.
* To open applications, you can use the 'open' command (e.g., 'open -a Notepad').
* For terminal commands that produce large outputs, redirect to a temporary file and use either:
  - 'less' for viewing
  - 'grep -n -B <lines before> -A <lines after> <query> <filename>' for searching
  - Or the built-in macOS text editor with 'open -e filename'
* When viewing web pages, consider using CMD+ or CMD- to adjust zoom for better visibility. Always scroll through entire pages before concluding content isn't present.
* Computer function calls may have latency. Where possible, batch multiple related actions into single function calls for efficiency.
* The current date is {datetime.today().strftime('%A, %B %-d, %Y')}.
</SYSTEM_CAPABILITY>

<IMPORTANT>
* When using browsers, if any startup/welcome screens appear, ignore them. Instead, click directly on the address bar and enter your URL or search term.
* For PDFs: If you need to read an entire document, download it using curl, then use macOS's built-in tools:
  - 'textutil -convert txt filename.pdf' for conversion
  - Or use 'open filename.pdf' to open in Preview for visual inspection
</IMPORTANT>"""


class ClaudeManager:
    def __init__(self):
        # init helcione
        self.client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'),
                                base_url="https://anthropic.helicone.ai",
                                default_headers={"Helicone-Auth": f"Bearer {os.environ.get('HELICONE_API_KEY')}"})

        self.system_prompt = SYSTEM_PROMPT
        self.only_n_most_recent_images = 3  # default value
        self.min_removal_threshold = 2  # default chunk size for removal

    def filter_recent_images(self, messages: List[dict], images_to_keep: int = None) -> List[dict]:
        """
        Filter messages to keep only N most recent images in tool results.
        """
        if images_to_keep is None:
            return messages

        # Find all tool result blocks that contain images
        tool_result_blocks = [
            item
            for message in messages
            for item in (message["content"] if isinstance(message["content"], list) else [])
            if isinstance(item, dict) and item.get("type") == "tool_result"
        ]

        # Count total images
        total_images = sum(
            1
            for tool_result in tool_result_blocks
            for content in tool_result.get("content", [])
            if isinstance(content, dict) and content.get("type") == "image"
        )

        # Calculate images to remove
        images_to_remove = total_images - images_to_keep
        # Remove in chunks for better cache behavior
        images_to_remove -= images_to_remove % self.min_removal_threshold

        if images_to_remove <= 0:
            return messages

        # Filter images from tool results
        for tool_result in tool_result_blocks:
            if isinstance(tool_result.get("content"), list):
                new_content = []
                for content in tool_result.get("content", []):
                    if isinstance(content, dict) and content.get("type") == "image":
                        if images_to_remove > 0:
                            images_to_remove -= 1
                            continue
                    new_content.append(content)
                tool_result["content"] = new_content

        return messages
    
    def call_claude(self, conversation_history: list = None, max_retries: int = 1, only_n_most_recent_images: int = None, tool_collection: ToolCollection = None) -> Dict[str, Any]:
        retry_count = 0
        betas = [COMPUTER_USE_BETA_FLAG]
        filtered_conversation_history = self.filter_recent_images(conversation_history.copy(), only_n_most_recent_images)
        while retry_count < max_retries:
            try:
                raw_response = self.client.beta.messages.with_raw_response.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=4096,
                    system=self.system_prompt,
                    messages=filtered_conversation_history, 
                    betas=betas,
                    tools=tool_collection.to_params(),
                )
                response = raw_response.parse()
                return response
                
            except (APIStatusError, APIResponseValidationError) as e:
                raise e
                
            except APIError as e:
                return e
                
            except Exception as e:
                retry_count += 1
                if retry_count == max_retries:
                    raise Exception(f"Failed to get response from Claude after {max_retries} retries. Error: {str(e)}")
                time.sleep(2 ** retry_count)  # Exponential backoff
