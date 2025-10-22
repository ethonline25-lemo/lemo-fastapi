from fastapi import Request
from fastapi.responses import JSONResponse
from helpers.intent_detection import intent_detection
from cases.asking import asking
from helpers.get_session_details import get_session_details

async def query_handler(request: Request):
    try:
        session_id = request.query_params.get("session_id")
        body = await request.json()
        user_id = request.headers.get("Authorization")
        
        if not session_id or not user_id:
            return JSONResponse(content={"message": "Session ID or User ID is required"}, status_code=401)
        
        session_details = get_session_details(session_id, user_id)
        user_query = body.get("user_query")
        
        if not user_query:
            return JSONResponse(content={"message": "User query is required"}, status_code=400)
        
        domain = session_details.get("current_domain")
        current_page_url = session_details.get("current_url")
        
        if not current_page_url:
            return JSONResponse(content={"message": "Current page URL not found in session"}, status_code=400)
        
        intent = intent_detection(user_query, session_id)
        
        if intent.intent == "ask":
            answer = asking(user_query, domain, current_page_url, intent.scope, session_id)
            return JSONResponse(content={"answer": answer}, status_code=200)
        else:
            return JSONResponse(content={"message": "Intent not recognized", "intent": intent.intent}, status_code=200)
    
    except ValueError as e:
        print(f"[ERROR] ValueError in query_handler: {e}")
        return JSONResponse(content={"message": str(e)}, status_code=400)
    except Exception as e:
        print(f"[ERROR] Unexpected error in query_handler: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(content={"message": "Internal server error", "error": str(e)}, status_code=500)
