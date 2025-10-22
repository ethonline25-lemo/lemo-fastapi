from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.requests import Request
from fastapi.responses import Response
import requests
from controllers.query_handler import query_handler
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "Cookie"],
    
)

@app.get("/")
async def get():
    return {"message": "Hello, World!"}

@app.post("/query")
async def query(request: Request):
    return await query_handler(request)

@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def reverse_proxy(path: str, request: Request):
    target_url = f"http://localhost:3000/api/{path}"
    
    query_params = dict(request.query_params)
    headers = dict(request.headers)
    headers.pop("host", None)
    
    body = await request.body()
    
    cookies = dict(request.cookies)
    
    response = requests.request(
        method=request.method,
        url=target_url,
        params=query_params,
        headers=headers,
        cookies=cookies,
        data=body,
        allow_redirects=False
    )
    
    fastapi_response = Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )
    
    for cookie_name, cookie_value in response.cookies.items():
        fastapi_response.set_cookie(key=cookie_name, value=cookie_value)
    
    return fastapi_response
