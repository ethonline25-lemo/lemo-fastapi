import requests
from helpers.redis_functions import add_message_to_chat

def add_chats(session_id: str, message: str, message_type: str, detected_intent: str, user_id: str):
    try:
        # Validate inputs
        if not session_id or not user_id:
            print("[ERROR] Session ID and User ID are required")
            return {"status": "error", "message": "Session ID and User ID are required"}
        
        if not message:
            print("[ERROR] Message is required")
            return {"status": "error", "message": "Message is required"}
        
        if message_type not in ["user", "assistant", "system"]:
            print(f"[ERROR] Invalid message_type: {message_type}")
            return {"status": "error", "message": f"Invalid message_type: {message_type}. Must be user/assistant/system"}
        
        url = "http://localhost:3000/api/sessions/message"
        headers = {
            "Authorization": user_id,
            "Content-Type": "application/json"
        }
        data = {
            "session_id": session_id,
            "message": message,
            "message_type": message_type,
            "detected_intent": detected_intent
        }
        
        # Send message to external API
        try:
            response = requests.post(url, headers=headers, json=data, timeout=10)
            response.raise_for_status()
            print(f"[LOG] Message sent to external API for session {session_id}")
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Failed to send message to external API: {e}")
            # Continue to store in Redis even if external API fails
        
        # Store message in Redis
        result = add_message_to_chat(session_id, message, message_type, detected_intent)
        
        if result.get("status") == "error":
            print(f"[ERROR] Failed to store message in Redis: {result.get('message')}")
            return result
        
        print(f"[LOG] Message successfully added for session {session_id}")
        return {"status": "success", "message": "Message added"}
    
    except Exception as e:
        print(f"[ERROR] Unexpected error in add_chats: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": f"Failed to add message: {str(e)}"}
