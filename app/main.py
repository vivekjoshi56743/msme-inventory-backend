from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # <--- Import CORS Middleware
from app.core.firebase_config import initialize_firebase

# Initialize Firebase FIRST
initialize_firebase()

# NOW, import the routers
from app.api.routes import auth, users, products, dashboard

app = FastAPI(title="MSME Inventory Lite API")

# --- Add CORS Middleware ---
# This allows your frontend (running on localhost:5173) to communicate with your backend.
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods (GET, POST, etc.)
    allow_headers=["*"], # Allows all headers
)
# -------------------------


# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(products.router, prefix="/products", tags=["Products"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])

@app.get("/")
def read_root():
    return {"status": "API is running"}