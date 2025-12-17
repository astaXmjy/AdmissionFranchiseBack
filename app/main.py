from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine
from .models import Base
from .routers import auth, admin, franchise
from .config.settings import get_app_settings

settings = get_app_settings()

# Create FastAPI app
app = FastAPI(
    title="Admission Management System",
    description="API for managing student admissions with role-based access",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(franchise.router, prefix="/franchise", tags=["Franchise"])

# Startup event
@app.on_event("startup")
def on_startup():
    # Create all tables
    Base.metadata.create_all(bind=engine)

# Root endpoint
@app.get("/")
def read_root():
    return {"message": "Admission Management System API"}

# Health check
@app.get("/health")
def health_check():
    return {"status": "healthy"}
