from fastapi import APIRouter, Depends
from app.api.dependencies import get_current_user

router = APIRouter()

@router.get("/me", summary="Get current user's details")
def get_user_me(current_user: dict = Depends(get_current_user)):
    """
    A protected endpoint that returns the details of the authenticated user.
    The user's data is injected by the get_current_user dependency.
    """
    return {"uid": current_user.get("uid"), "email": current_user.get("email")}