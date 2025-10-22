from fastapi import Request
from fastapi.responses import JSONResponse
from helpers.intent_detection import intent_detection
from cases.asking import asking

async def query_handler(request: Request):
    session_id = request.query_params.get("session_id")
    body = await request.json()
    user_query = body.get("user_query")
    domain = body.get("domain", "")
    current_page_url = body.get("current_page_url", "")
    intent = intent_detection(user_query, session_id)
    if intent.intent == "ask":
        answer = asking(user_query, domain, current_page_url, intent.scope, session_id)
        return JSONResponse(content={"answer": answer}, status_code=200)
    else:
        return JSONResponse(content={"message": "Intent not recognized"}, status_code=200)
