from fastapi import Request, HTTPException, status
from prisma import Prisma

prisma = Prisma()

async def get_current_user(request: Request):
    """
    Dependency to authenticate user via wallet address in Authorization header
    """
    if not prisma.is_connected():
        await prisma.connect()
    
    # Get wallet address from Authorization header
    wallet_address = request.headers.get("authorization")
    
    if not wallet_address:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authenticated"
        )
    
    # Find user in database
    user = await prisma.users.find_unique(
        where={"wallet_address": wallet_address}
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Return the user object
    return user