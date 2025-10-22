from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.requests import Request
from controllers.query_handler import query_handler
from routes.authentication_routes import router as authentication_routes
from routes.session_routes import router as session_routes

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

app.include_router(authentication_routes, prefix="/auth")
app.include_router(session_routes, prefix="/sessions")

# @app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
# async def reverse_proxy(path: str, request: Request):
#     target_url = f"http://localhost:3000/api/{path}"
    
#     query_params = dict(request.query_params)
#     headers = dict(request.headers)
#     headers.pop("host", None)
    
#     body = await request.body()
    
#     cookies = dict(request.cookies)
    
#     response = requests.request(
#         method=request.method,
#         url=target_url,
#         params=query_params,
#         headers=headers,
#         cookies=cookies,
#         data=body,
#         allow_redirects=False
#     )
    
#     fastapi_response = Response(
#         content=response.content,
#         status_code=response.status_code,
#         headers=dict(response.headers)
#     )
    
#     for cookie_name, cookie_value in response.cookies.items():
#         fastapi_response.set_cookie(key=cookie_name, value=cookie_value)
    
#     return fastapi_response
