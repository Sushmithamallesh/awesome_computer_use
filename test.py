import requests
import json

def test_chat():
    url = "http://127.0.0.1:5000/api/chat"  # Your Flask endpoint
    
    payload = {
        "message": "Take a screenshot and open google.com",
        "conversation_history": []  # Empty history for first message
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()  # Raise exception for bad status codes
        
        result = response.json()
        print("Response status:", result["status"])
        print("\nFull conversation:")
        for message in result["messages"]:
            print(f"\nRole: {message['role']}")
            for content in message['content']:
                print(f"Type: {content['type']}")
                if content['type'] == 'text':
                    print(f"Text: {content['text']}")
                elif content['type'] == 'tool_use':
                    print(f"Tool: {content['name']}")
                    print(f"Input: {content['input']}")
                elif content['type'] == 'tool_result':
                    if 'output' in content:
                        print(f"Output: {content['output']}")
                    if 'error' in content:
                        print(f"Error: {content['error']}")

    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
    except json.JSONDecodeError as e:
        print(f"Error parsing response: {e}")

if __name__ == "__main__":
    test_chat()