from fastapi import APIRouter, HTTPException
from firebase_admin import auth

from app.models.user import UserCreate # <-- Importing from our new models folder

router = APIRouter()

@router.post("/register", status_code=201)
def create_user(user_data: UserCreate):
    """
    Endpoint to register a new user with email and password.
    """
    try:
        user = auth.create_user(
            email=user_data.email,
            password=user_data.password
        )
        return {"message": f"Successfully created user: {user.uid}", "email": user.email}
    except auth.EmailAlreadyExistsError:
        raise HTTPException(
            status_code=400,
            detail=f"The email {user_data.email} is already registered."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {e}"
        )