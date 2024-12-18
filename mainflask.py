from flask import Flask, request, jsonify, session
from flask_cors import CORS
from core.loop import ChatLoop
from core.sender import Sender
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)  # for session management
CORS(app)

# Global chat loop instance
chat_loop = ChatLoop()

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    prompt = data.get('message')
    conversation_history = data.get('conversation_history', [])
    
    # Create user message
    user_message = {
        "role": Sender.USER,
        "content": [{
            "type": "text",
            "text": prompt
        }]
    }
    
    # Add to history
    conversation_history.append(user_message)
    
    # Get response from chat loop
    try:
        final_messages = chat_loop.get_response(
            conversation_history=conversation_history
        )
        return jsonify({
            "status": "success",
            "messages": final_messages
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@app.route('/api/config', methods=['POST'])
def update_config():
    data = request.json
    try:
        n_images = data.get('only_n_most_recent_images', 1)
        chat_loop.only_n_most_recent_images = n_images
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False, host='127.0.0.1', port=5000)