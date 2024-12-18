import streamlit as st
from core.loop import ChatLoop
from anthropic.types import Message, MessageParam, ContentBlock, TextBlockParam, ImageBlockParam, ToolUseBlockParam, ToolResultBlockParam, Usage
import os
from dotenv import load_dotenv
from core.claude import BetaTextBlockParam, BetaToolUseBlockParam, BetaToolResultBlockParam
from core.sender import Sender
# Load environment variables
load_dotenv()

def render_message(message):
    """Callback function to render messages and tool outputs"""
    with st.chat_message(message["role"]):
        for block in message["content"]:
            if block["type"] == "text":
                st.markdown(block["text"])
            elif block["type"] == "tool_use":
                st.code(f"Tool Use: {block['name']}\nInput: {block['input']}")
            elif block["type"] == "tool_result":
                tool_result = st.session_state.tools.get(block["tool_use_id"])
                if tool_result:
                    if tool_result.output:
                        st.code(tool_result.output)
                    if tool_result.error:
                        st.error(tool_result.error)
                    if hasattr(tool_result, 'screenshot') and tool_result.screenshot:
                        st.image(tool_result.screenshot)

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


if 'chat_loop' not in st.session_state:
    st.session_state.chat_loop = ChatLoop()

# Initialize session states
if 'only_n_most_recent_images' not in st.session_state:
    st.session_state.only_n_most_recent_images = 1

# Add a sidebar configuration
with st.sidebar:
    st.number_input(
        "Keep N most recent images",
        min_value=1,
        max_value=10,
        value=st.session_state.only_n_most_recent_images,
        key="only_n_most_recent_images",
        help="To reduce tokens, only keep this many recent images in the conversation"
    )
    
    # Update chat loop with new value
    st.session_state.chat_loop.only_n_most_recent_images = st.session_state.only_n_most_recent_images
    
# Display chat history
for message in st.session_state.messages:
    render_message(message)

# Chat input and message flow
if prompt := st.chat_input("What would you like me to do?"):
    user_message = {
        "role": Sender.USER,
        "content": [{
            "type": "text",
            "text": prompt
        }]
    }
    st.session_state.messages.append(user_message)
    render_message(user_message)

    # Pass the render_message callback to Claude manager
    with st.spinner("Processing..."):
        final_messages = st.session_state.chat_loop.get_response(
            conversation_history=st.session_state.messages,
            render_callback=render_message
        )
    
    st.session_state.messages = final_messages
    
