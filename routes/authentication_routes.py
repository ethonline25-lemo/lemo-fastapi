from fastapi import APIRouter, Request
from controllers.authentication import AuthenticateUser, CreateUser

router = APIRouter()

@router.get("/{walletAddress}")
async def authenticate_user(req: Request):
    return await AuthenticateUser(req)

@router.post("/{walletAddress}")
async def create_user(req: Request):
    return await CreateUser(req)
