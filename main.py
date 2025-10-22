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