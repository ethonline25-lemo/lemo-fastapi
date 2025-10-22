from fastapi import Request
from fastapi.responses import JSONResponse
from helpers.intent_detection import intent_detection
from cases.asking import asking
from helpers.get_session_details import get_session_details
from helpers.redis_functions import get_chat_history, delete_chat_history, store_chat_history
from helpers.add_chats import add_chats
async def query_handler(request: Request):
    try:
        session_id = request.query_params.get("session_id")
        body = await request.json()
        user_id = request.headers.get("Authorization")
        
        if not session_id or not user_id:
            return JSONResponse(content={"message": "Session ID or User ID is required"}, status_code=401)
        
        session_details = await get_session_details(session_id, user_id)
        user_query = body.get("user_query")
        
        if not user_query:
            return JSONResponse(content={"message": "User query is required"}, status_code=400)
        
        domain = session_details.get("current_domain")
        current_page_url = session_details.get("current_url")
        
        if not current_page_url:
            return JSONResponse(content={"message": "Current page URL not found in session"}, status_code=400)

        # Sync chat history from DB to Redis if needed
        chat_history_redis = get_chat_history(session_id)
        db_messages = session_details.get("chat_messages", [])
        
        # Convert DB messages to Redis format (remove extra fields like id, session_id, user_id)
        redis_format_messages = []
        for msg in db_messages:
            redis_format_messages.append({
                "message": msg.get("message"),
                "message_type": msg.get("message_type"),
                "detected_intent": msg.get("detected_intent"),
                "created_at": msg.get("created_at")
            })
        
        # Sync logic: if Redis has fewer messages than DB, resync from DB
        redis_count = len(chat_history_redis)
        db_count = len(redis_format_messages)
        
        if redis_count < db_count:
            print(f"[LOG] Syncing chat history: Redis has {redis_count} messages, DB has {db_count} messages")
            delete_chat_history(session_id)
            if redis_format_messages:
                store_chat_history(session_id, redis_format_messages)
            print(f"[LOG] Chat history synced successfully")
        
        # Detect intent
        intent = intent_detection(user_query, session_id)
        print(f"[LOG] Detected intent: {intent.intent}, scope: {intent.scope}, confidence: {intent.intent_confidence}")
        
        # Process based on intent
        answer = None
        res = None
        
        if intent.intent == "ask":
            if intent.scope == "chat_history":
                answer = intent.message_forward.summary
            else:
                print(f"[LOG] Processing 'ask' intent with scope: {intent.scope}")
                answer = asking(user_query, domain, current_page_url, intent.scope, session_id)
            print(f"[LOG] Got answer: {answer[:100] if answer else 'None'}...")
            res = JSONResponse(content={"answer": answer}, status_code=200)
        else:
            print(f"[LOG] Intent '{intent.intent}' not recognized as 'ask'")
            answer = "I didn't understand that. Could you please rephrase?"
            res = JSONResponse(content={"message": "Intent not recognized", "intent": intent.intent, "answer": answer}, status_code=200)
    
        # Add messages to both DB and Redis
        await add_chats(session_id, user_query, "user", intent.intent, user_id)
        if answer:
            await add_chats(session_id, answer, "assistant", intent.intent, user_id)
        
        return res
    
    except ValueError as e:
        print(f"[ERROR] ValueError in query_handler: {e}")
        return JSONResponse(content={"message": str(e)}, status_code=400)
    except Exception as e:
        print(f"[ERROR] Unexpected error in query_handler: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(content={"message": "Internal server error", "error": str(e)}, status_code=500)
