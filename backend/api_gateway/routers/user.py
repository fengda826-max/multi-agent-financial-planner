from fastapi import APIRouter, Depends
from shared.schemas.user import UserResponse
from api_gateway.middleware.auth import get_current_user

router = APIRouter()


@router.get("/me", response_model=dict)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    return {"user_id": current_user["user_id"]}
