from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.core.firebase_config import initialize_firebase
from app.core.monitoring import logging_middleware, get_metrics
from app.api.dependencies import get_current_user
import os

# Initialize Firebase FIRST, before any other app imports that might use it
initialize_firebase()

# NOW, import the routers that depend on the initialized app
from app.api.routes import auth, users, products, dashboard


app = FastAPI(title="MSME Inventory Lite API")
app.middleware("http")(logging_middleware)

# --- Updated CORS Middleware ---
# Reads allowed origins from an environment variable for production,
# but still allows localhost for local development.
allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
origins = [origin.strip() for origin in allowed_origins_str.split(',')]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all the API routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(products.router, prefix="/products", tags=["Products"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])

# Add the root and monitoring endpoints
@app.get("/", tags=["Monitoring"])
def read_root():
    """A simple root endpoint to confirm the API is running."""
    return {"status": "API is running"}

@app.get("/health", tags=["Monitoring"])
def health_check():
    """A simple health check endpoint required by the assignment."""
    return {"status": "ok"}

@app.get("/metrics", tags=["Monitoring"])
def metrics():
    """An open endpoint to get runtime metrics for the application."""
    return get_metrics()