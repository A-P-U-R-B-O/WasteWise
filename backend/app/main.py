"""
WasteWise FastAPI Application
Main application entry point with all configurations
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import time
import logging
from pathlib import Path
import os

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.database import initialize_firebase, close_firebase
from app.services.gemini_service import get_gemini_service

# Import routes
from app.api.routes import waste
# from app.api.routes import user, auth, leaderboard

# ==================== LOG DIRECTORY SETUP (EARLY) ====================
# Ensure log directory exists before configuring logging!
if settings.LOG_FILE:
    log_dir = os.path.dirname(settings.LOG_FILE)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

# ==================== CONFIGURE LOGGING ====================
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(settings.LOG_FILE) if settings.LOG_FILE else logging.NullHandler()
    ]
)

logger = logging.getLogger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# ==================== LIFESPAN EVENTS ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan events - runs on startup and shutdown
    """
    # Startup
    logger.info("🚀 Starting WasteWise API...")

    # Initialize Firebase
    try:
        initialize_firebase()
        logger.info("✅ Firebase initialized")
    except Exception as e:
        logger.error(f"❌ Firebase initialization failed: {str(e)}")
        # Continue anyway for development

    # Validate Gemini API
    try:
        gemini_service = get_gemini_service()
        if gemini_service.validate_api_key():
            logger.info("✅ Gemini AI connected")
        else:
            logger.warning("⚠️ Gemini API key validation failed")
    except Exception as e:
        logger.error(f"❌ Gemini initialization failed: {str(e)}")

    # Create required directories (for uploaded files, etc.)
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    logger.info(f"🌍 Environment: {settings.ENVIRONMENT}")
    logger.info(f"🔧 Debug mode: {settings.DEBUG}")
    logger.info("✅ Application startup complete")

    yield

    # Shutdown
    logger.info("🛑 Shutting down WasteWise API...")

    try:
        close_firebase()
        logger.info("✅ Firebase connection closed")
    except Exception as e:
        logger.error(f"❌ Firebase shutdown error: {str(e)}")

    logger.info("✅ Application shutdown complete")

# ==================== CREATE APP ====================

app = FastAPI(
    **settings.fastapi_kwargs,
    lifespan=lifespan
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ==================== MIDDLEWARE ====================

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count", "X-Page", "X-Per-Page"]
)

# GZip Compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Trusted Host (security)
if settings.is_production:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=[
            "*.wastewise.com",
            "wastewise.com",
            "*.onrender.com",          # Accept ALL onrender subdomains
            "wastewise-r6fh.onrender.com" 
        ]
    )

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with timing"""
    start_time = time.time()

    # Process request
    response = await call_next(request)

    # Calculate duration
    duration = time.time() - start_time

    # Log request
    logger.info(
        f"{request.method} {request.url.path} | "
        f"Status: {response.status_code} | "
        f"Duration: {duration:.3f}s | "
        f"Client: {request.client.host if request.client else 'unknown'}"
    )

    # Add custom headers
    response.headers["X-Process-Time"] = str(duration)
    response.headers["X-API-Version"] = settings.APP_VERSION

    return response

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    return response

# ==================== EXCEPTION HANDLERS ====================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    logger.warning(f"Validation error on {request.url.path}: {exc.errors()}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": "Validation Error",
            "message": "Invalid request data",
            "details": exc.errors()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions"""
    logger.error(f"Unhandled exception on {request.url.path}: {str(exc)}", exc_info=True)

    # Don't expose internal errors in production
    if settings.is_production:
        message = "An internal error occurred"
    else:
        message = str(exc)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "Internal Server Error",
            "message": message
        }
    )

# ==================== ROOT ROUTES ====================

@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint - API information
    """
    return {
        "success": True,
        "message": "Welcome to WasteWise API",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "documentation": "/docs" if not settings.is_production else None,
        "endpoints": {
            "health": "/health",
            "api": settings.API_V1_PREFIX
        }
    }

@app.get("/health", tags=["Health"])
@limiter.limit("30/minute")
async def health_check(request: Request):
    """
    Health check endpoint
    Returns API status and service health
    """
    # Check Gemini service
    gemini_status = "unknown"
    try:
        gemini_service = get_gemini_service()
        gemini_status = "healthy" if gemini_service.validate_api_key() else "unhealthy"
    except Exception as e:
        gemini_status = f"error: {str(e)}"
        logger.error(f"Gemini health check failed: {str(e)}")

    # Check Firebase
    firebase_status = "unknown"
    try:
        from app.core.database import get_firestore_client
        db = get_firestore_client()
        firebase_status = "healthy" if db else "unhealthy"
    except Exception as e:
        firebase_status = f"error: {str(e)}"
        logger.error(f"Firebase health check failed: {str(e)}")

    return {
        "success": True,
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "services": {
            "api": "healthy",
            "gemini_ai": gemini_status,
            "firebase": firebase_status
        },
        "uptime": "N/A"  # Can be calculated from startup time
    }

@app.get("/info", tags=["Info"])
async def api_info():
    """
    Detailed API information
    """
    return {
        "success": True,
        "api": {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "description": settings.APP_DESCRIPTION,
            "environment": settings.ENVIRONMENT
        },
        "features": {
            "waste_identification": True,
            "gamification": True,
            "leaderboard": True,
            "user_authentication": True,
            "scan_history": True,
            "educational_content": True
        },
        "supported_waste_categories": settings.WASTE_CATEGORIES,
        "limits": {
            "max_upload_size_mb": settings.MAX_UPLOAD_SIZE / (1024 * 1024),
            "allowed_image_types": settings.ALLOWED_IMAGE_TYPES,
            "rate_limit_per_minute": settings.RATE_LIMIT_PER_MINUTE,
            "scan_limit_per_hour": settings.RATE_LIMIT_SCAN_PER_HOUR
        },
        "ai_model": {
            "provider": "Google Gemini",
            "model": settings.GEMINI_MODEL,
            "capabilities": [
                "Image recognition",
                "Waste classification",
                "Disposal guidance",
                "Environmental impact analysis"
            ]
        }
    }

# ==================== TEST ENDPOINTS (Development Only) ====================

if not settings.is_production:

    @app.post("/test/upload", tags=["Testing"])
    async def test_image_upload(request: Request):
        """
        Test endpoint for image upload
        Only available in development
        """
        from fastapi import File, UploadFile

        @app.post("/test/upload-file")
        async def upload_test_file(file: UploadFile = File(...)):
            from app.utils.image_processor import process_uploaded_image

            try:
                # Read file
                file_data = await file.read()

                # Process
                result = process_uploaded_image(file_data, file.filename)

                return {
                    "success": True,
                    "message": "Image processed successfully",
                    "metadata": result["metadata"],
                    "image_hash": result["image_hash"]
                }
            except Exception as e:
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "error": str(e)
                    }
                )

        return await upload_test_file(request)

    @app.get("/test/gemini", tags=["Testing"])
    async def test_gemini():
        """
        Test Gemini AI connection
        Only available in development
        """
        try:
            gemini_service = get_gemini_service()

            # Simple test
            test_response = gemini_service.model.generate_content(
                "Respond with a JSON object: {\"status\": \"working\", \"message\": \"Gemini AI is operational\"}"
            )

            return {
                "success": True,
                "gemini_status": "connected",
                "model": settings.GEMINI_MODEL,
                "test_response": test_response.text
            }
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": str(e)
                }
            )

    @app.get("/test/config", tags=["Testing"])
    async def test_config():
        """
        View current configuration
        Only available in development
        """
        return {
            "success": True,
            "config": {
                "app_name": settings.APP_NAME,
                "version": settings.APP_VERSION,
                "environment": settings.ENVIRONMENT,
                "debug": settings.DEBUG,
                "gemini_model": settings.GEMINI_MODEL,
                "upload_dir": settings.UPLOAD_DIR,
                "max_upload_size_mb": settings.MAX_UPLOAD_SIZE / (1024 * 1024),
                "cors_origins": settings.BACKEND_CORS_ORIGINS,
                "waste_categories": settings.WASTE_CATEGORIES
            }
        }

# ==================== API ROUTES ====================

# Include API routers
from app.api.routes import waste
# from app.api.routes import user, auth, leaderboard

app.include_router(
    waste.router,
    prefix=f"{settings.API_V1_PREFIX}/waste",
    tags=["Waste Identification"]
)

"""
# These are commented out for now - we'll uncomment as we create the route files
app.include_router(
    auth.router,
    prefix=f"{settings.API_V1_PREFIX}/auth",
    tags=["Authentication"]
)

app.include_router(
    user.router,
    prefix=f"{settings.API_V1_PREFIX}/users",
    tags=["Users"]
)

app.include_router(
    leaderboard.router,
    prefix=f"{settings.API_V1_PREFIX}/leaderboard",
    tags=["Leaderboard & Gamification"]
)
"""

# ==================== STARTUP MESSAGE ====================

if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print(f"🌍 WasteWise API v{settings.APP_VERSION}")
    print(f"🔧 Environment: {settings.ENVIRONMENT}")
    print(f"📍 Starting server at http://localhost:8000")
    print(f"📚 API Docs at http://localhost:8000/docs")
    print("=" * 60)

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
)
