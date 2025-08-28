from fastapi import FastAPI
from app.core.firebase_config import initialize_firebase

# Initialize Firebase FIRST, before any other app imports
initialize_firebase()

# NOW, import the routers that depend on the initialized app
from app.api.routes import auth, users, products

app = FastAPI(title="MSME Inventory Lite API")

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(products.router, prefix="/products", tags=["Products"])

@app.get("/")
def read_root():
    return {"status": "API is running"}