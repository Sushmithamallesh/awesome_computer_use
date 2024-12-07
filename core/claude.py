from anthropic import Anthropic
from typing import Dict, Any
import os
from datetime import datetime
from utils.utils import take_screenshot
from anthropic.types.beta import (
    BetaContentBlockParam,
    BetaImageBlockParam,
    BetaMessage,
    BetaMessageParam,
    BetaTextBlock,
    BetaTextBlockParam,
    BetaToolResultBlockParam,
    BetaToolUseBlockParam,
)
import time


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
        
    def get_response(self, message: str, conversation_history: list = None, max_retries: int = 3) -> Dict[str, Any]:
        """Get response from Claude with message"""
        retry_count = 0
        backoff_time = 1
                    
            # Add to Claude history
            claude_user_message = Message(role="user", content=user_input)
            st.session_state.claude_history.append(claude_user_message)
            
        while retry_count < max_retries:
            try:
                print(f"Sending message to Claude: {message}")
                print(f"Conversation history: {conversation_history}")
                response = self.client.messages.create(
                    model="claude-3-opus-20240229",
                    max_tokens=4096,
                    system=self.system_prompt,
                    messages=conversation_history if conversation_history else [{
                        "role": "user",
                        "content": message
                    }]
                )
                return response
                
            except Exception as e:
                retry_count += 1
                if retry_count == max_retries:
                    raise Exception(f"Failed to get response after {max_retries} attempts. Error: {str(e)}")
                
                # Exponential backoff: 1s, 2s, 4s, etc.
                time.sleep(backoff_time)
                backoff_time *= 2


        
    def loop(self, message: str, conversation_hist