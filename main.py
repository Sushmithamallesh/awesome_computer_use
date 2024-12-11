import streamlit as st
from core.loop import ChatLoop
from core.claude import ClaudeManager
from anthropic.types import Message, MessageParam, ContentBlock, TextBlockParam, ImageBlockParam, ToolUseBlockParam, ToolResultBlockParam, Usage
import os
from dotenv import load_dotenv
from core.claude import Sender
from core.claude import BetaTextBlockParam, BetaToolUseBlockParam, BetaToolResultBlockParam
# Load environment variables
load_dotenv()

# Configure Streamlit page
st.set_page_config(
    page_title="Awesome Computer Assistant",
    page_icon="💻",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize session states
if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'tools' not in st.session_state:
    st.session_state.tools = {}

if 'claude_history' not in st.session_state:
    st.session_state.claude_history: list[Message] = []

if 'chat_loop' not in st.session_state:
    st.session_state.chat_loop = ChatLoop()

if 'claude_manager' not in st.session_state:
    st.session_state.claude_manager = ClaudeManager()

# Custom CSS for dark theme and message styling
st.markdown("""
    <style>
    .stTextInput > div > div > input {
        background-color: #2b303b;
        color: white;
    }
    .user-message {
        background-color: #2b303b;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
    }
    .assistant-message {
        background-color: #1a1f2b;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
    }
    </style>
""", unsafe_allow_html=True)

# Chat title
st.title("Awesome Computer Assistant")


# Rest of your chat interface code...
# Display chat messages
chat_container = st.container()
with chat_container:
    for message in st.session_state.messages:
        if message.get("role") == "user":
            st.markdown(f"""
                <div class="user-message">
                    {message.get("content")}
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div class="assistant-message">
                    {message.get("content")}
                </div>
            """, unsafe_allow_html=True)
            if message.get("screenshot"):
                st.image(message.get("screenshot"))

# Input area
with st.container():
    with st.form(key="chat_input_form", clear_on_submit=True):
        user_input = st.text_input("Type your message:", key="user_input")
        submit_button = st.form_submit_button("Send")

    if submit_button and user_input:
        # Add user message
        user_message = {
            "role": Sender.USER,
            "content": [
                BetaTextBlockParam(type="text", text=user_input)
            ]
        }
        st.session_state.messages.append(user_message)
                
        # Get Claude's response
        response = st.session_state.claude_manager.get_response(
            conversation_history=st.session_state.messages
        )
    
        # Convert Claude's response to our message format
        claude_message = {
            "role": Sender.BOT,
            "content": []
        }
        
        # Process the response content
        for content in response.get("content", []):
            if content.type == "text":
                claude_message["content"].append({
                    "type": "text",
                    "text": content.text
                })
            elif content.type == "tool_use":
                tool_result = st.session_state.chat_loop.process_tool_calls(content)
                # Store tool result
                st.session_state.tools[content.id] = tool_result
                # Add tool use block
                claude_message["content"].append({
                    "type": "tool_use",
                    "id": content.id,
                    "name": content.name,
                    "input": content.input
                })
                # Add tool result block
                claude_message["content"].append({
                    "type": "tool_result",
                    "tool_use_id": content.id,
                    "content": tool_result.output if tool_result.output else tool_result.error,
                    "is_error": bool(tool_result.error)
                })
        
        st.session_state.messages.append(claude_message)
        st.rerun()
        
        # Update message rendering
        for message in st.session_state.messages:
            if isinstance(message.get("content"), list):
                for block in message.get("content", []):
                    if block.get("type") == "text":
                        st.markdown(f"""
                            <div class="{message.get('role')}-message">
                                {block.get('text')}
                            </div>
                        """, unsafe_allow_html=True)
                    elif block.get("type") == "tool_result":
                        tool_result = st.session_state.tools.get(block.get("tool_use_id"))
                        if tool_result and tool_result.screenshot:
                            st.image(tool_result.screenshot)