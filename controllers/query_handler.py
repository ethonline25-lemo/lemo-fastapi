from fastapi import Request
from fastapi.responses import JSONResponse
from helpers.intent_detection import intent_detection
from cases.asking import asking
from helpers.get_session_details import get_session_details
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

        # Detect intent
        intent = intent_detection(user_query)
        print(f"[LOG] Detected intent: {intent.intent}, scope: {intent.scope}, message_forward: {intent.message_forward}")
        
        # Process based on intent - ALWAYS handle intelligently
        answer = None
        res = None
        
        # Determine the best handling approach
        chat_history = "\n".join([f"{msg.get('message_type')}: {msg.get('message')}" for msg in session_details.get("chat_messages")])
        
        # For current_page scope, always use current_page_asking for context-aware responses
        if intent.scope == "current_page":
            print(f"[LOG] Processing '{intent.intent}' intent with scope: current_page")
            from cases.asking import current_page_asking
            # Use the ORIGINAL user query, not the modified message_forward
            answer = current_page_asking(user_query, current_page_url)
        else:
            # For other scopes, use the general asking function
            print(f"[LOG] Processing '{intent.intent}' intent with scope: {intent.scope}")
            answer = asking(user_query, domain, current_page_url, intent.scope, session_id, chat_history)
        
        print(f"[LOG] Got answer: {answer[:100] if answer else 'None'}...")
        res = JSONResponse(content={"answer": answer}, status_code=200)
    
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
    except Exception as e:
        print(f"[ERROR] Unexpected error in query_handler: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(content={"message": "Internal server error", "error": str(e)}, status_code=500)

