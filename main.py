import streamlit as st
from core.loop import ChatLoop
from core.claude import ClaudeManager
from anthropic.types import Message, MessageParam, ContentBlock, TextBlockParam, ImageBlockParam, ToolUseBlockParam, ToolResultBlockParam, Usage
import os
from dotenv import load_dotenv
from core.models import UIMessage 

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
if 'ui_messages' not in st.session_state:
    st.session_state.ui_messages: list[UIMessage] = []

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
    for message in st.session_state.ui_messages:
        if message.role == "user":
            st.markdown(f"""
                <div class="user-message">
                    {message.content}
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div class="assistant-message">
                    {message.content}
                </div>
            """, unsafe_allow_html=True)
            if message.screenshot:
                st.image(message.screenshot)

# Input area
with st.container():
    with st.form(key="chat_input_form", clear_on_submit=True):
        user_input = st.text_input("Type your message:", key="user_input")
        submit_button = st.form_submit_button("Send")

        if submit_button and user_input:
            # Add to UI messages
            user_ui_message = UIMessage(role="user", content=user_input)
            st.session_state.ui_messages.append(user_ui_message)
            
            # Get Claude's analysis and instructions
            claude_response = st.session_state.claude_manager.get_response(
                message=user_input,
                conversation_history=st.session_state.claude_history,
            )

            # Execute tool based on Claude's instructions
            tool_response = st.session_state.chat_loop.process_message(claude_response)
            
            # Create response messages
            response_content = f"{claude_response['message']}\n\nAction result: {tool_response['message']}"
            
            # Add to UI messages
            assistant_ui_message = UIMessage(
                role="assistant",
                content=response_content
            )
            st.session_state.ui_messages.append(assistant_ui_message)
            
            # Add to Claude history
            claude_assistant_message = Message(
                role="assistant",
                content=response_content
            )
            st.session_state.claude_history.append(claude_assistant_message)
            
            st.rerun() 