from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from firebase_admin import auth

# This scheme will require a "Bearer" token in the Authorization header
bearer_scheme = HTTPBearer()

def get_current_user(token: str = Depends(bearer_scheme)) -> dict:
    """
    Dependency to verify the Firebase ID token and get the current user.
    """
    try:
        # The token object from HTTPBearer has a 'credentials' attribute
        decoded_token = auth.verify_id_token(token.credentials)
        return decoded_token
    except Exception as e:
        # Handle various errors like expired, revoked, or invalid tokens
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )