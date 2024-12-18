from core.loop import ChatLoop
from dotenv import load_dotenv
def main():
    # Single instance, single thread, no complications
    load_dotenv()
    chat_loop = ChatLoop()
    
    while True:
        # Simple input/output loop
        user_input = input("What would you like me to do? (or 'quit' to exit): ")
        if user_input.lower() == 'quit':
            break
            
        messages = chat_loop.get_response(
            conversation_history=[{
                "role": "user",
                "content": [{"type": "text", "text": user_input}]
            }]
        )
        
        # Print responses
        for message in messages:
            print(f"\n{message['role']}:")
            for content in message['content']:
                print(content)

if __name__ == "__main__":
    main()