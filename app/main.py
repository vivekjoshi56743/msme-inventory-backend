from fastapi import FastAPI
from app.core.firebase_config import initialize_firebase
from app.api.routes import auth, users # <--- Import the new users router

# Initialize Firebase on startup
initialize_firebase()

app = FastAPI(title="MSME Inventory Lite API")

# Include the authentication router
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# Include the new users router
app.include_router(users.router, prefix="/users", tags=["Users"]) # <--- Add this line

@app.get("/")
def read_root():
    return {"status": "API is running"}