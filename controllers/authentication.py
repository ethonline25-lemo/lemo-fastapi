from fastapi import Request
from fastapi.responses import JSONResponse
from prisma import Prisma
import json

prisma = Prisma()

async def AuthenticateUser(req: Request):
    if not prisma.is_connected():
        await prisma.connect()
    try:
        walletAddress = req.path_params.get("walletAddress")

        if not walletAddress or not isinstance(walletAddress, str) or len(walletAddress.strip()) == 0:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Invalid wallet address provided"
                }
            )

        normalizedWalletAddress = walletAddress.strip()

        # removed `select` — prisma-client-py doesn't accept `select` here
        dbUser = await prisma.users.find_unique(
            where={"wallet_address": normalizedWalletAddress}
        )

        if not dbUser:
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "error": "User not found"
                }
            )

        # dbUser is a model instance; access fields as attributes
        if not dbUser.is_active:
            return JSONResponse(
                status_code=403,
                content={
                    "success": False,
                    "error": "User account is inactive"
                }
            )

        # Return only the fields you want by building a dict
        user_data = {
            "id": dbUser.id,
            "email": dbUser.email,
            "first_name": dbUser.first_name,
            "last_name": dbUser.last_name,
            "wallet_address": dbUser.wallet_address,
            "is_active": dbUser.is_active,
        }

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "User authenticated successfully",
                "data": {
                    "user": user_data
                }
            }
        )

    except Exception as error:
        print("Error during authentication:", {
            "error": str(error),
            "walletAddress": req.path_params.get("walletAddress")
        })
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Internal server error"
            }
        )


async def CreateUser(req: Request):
    if not prisma.is_connected():
        await prisma.connect()
    try:
        body = await req.json()
        walletAddress = req.path_params.get("walletAddress")
        email = body.get("email")
        firstName = body.get("firstName")
        lastName = body.get("lastName")
        otherDetails = body.get("otherDetails")

        if not walletAddress or not isinstance(walletAddress, str) or len(walletAddress.strip()) == 0:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Valid wallet address is required"
                }
            )

        if not email or not isinstance(email, str) or "@" not in email:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Valid email is required"
                }
            )

        if not firstName or not isinstance(firstName, str) or len(firstName.strip()) == 0:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "First name is required"
                }
            )

        if not lastName or not isinstance(lastName, str) or len(lastName.strip()) == 0:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Last name is required"
                }
            )

        normalizedWalletAddress = walletAddress.strip()
        normalizedEmail = email.strip()

        existingUser = await prisma.users.find_first(
            where={
                "OR": [
                    {"wallet_address": normalizedWalletAddress},
                    {"email": normalizedEmail},
                ]
            }
        )

        if existingUser:
            if existingUser.wallet_address == normalizedWalletAddress:
                return JSONResponse(
                    status_code=409,
                    content={
                        "success": False,
                        "error": "User with this wallet address already exists"
                    }
                )
            if existingUser.email == normalizedEmail:
                return JSONResponse(
                    status_code=409,
                    content={
                        "success": False,
                        "error": "User with this email already exists"
                    }
                )
        other_details_value = None
        if otherDetails:
            if isinstance(otherDetails, dict):
                other_details_value = json.dumps(otherDetails)
            elif isinstance(otherDetails, str):
                other_details_value = otherDetails
            else:
                other_details_value = json.dumps(otherDetails)

        # Create user with proper JSON handling
        create_data = {
            "id": normalizedWalletAddress,
            "wallet_address": normalizedWalletAddress,
            "email": normalizedEmail,
            "first_name": firstName.strip(),
            "last_name": lastName.strip(),
            "is_active": True,
        }
        
        # Only add other_details if it has a value
        if other_details_value is not None:
            create_data["other_details"] = other_details_value

        # create returns the full model instance
        newUser = await prisma.users.create(
            data=create_data,
        )

        user_data = {
            "id": newUser.id,
            "email": newUser.email,
            "first_name": newUser.first_name,
            "last_name": newUser.last_name,
            "wallet_address": newUser.wallet_address,
        }

        return JSONResponse(
            status_code=201,
            content={
                "success": True,
                "message": "User created successfully",
                "data": {
                    "user": user_data
                }
            }
        )

    except Exception as error:
        print("Error during user creation:", {
            "error": str(error),
            "walletAddress": req.path_params.get("walletAddress"),
            "email": body.get("email") if body else None
        })

        if hasattr(error, "code") and error.code == "P2002":
            return JSONResponse(
                status_code=409,
                content={
                    "success": False,
                    "error": "User with this wallet address or email already exists"
                }
            )

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Internal server error"
            }
        )
