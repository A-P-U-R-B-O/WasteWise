"""
Application Configuration
Handles all environment variables and app settings
"""

from functools import lru_cache
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field, validator
import os
from pathlib import Path

# Get the base directory
BASE_DIR = Path(__file__).resolve().parent.parent. parent


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    """
    
    # ==================== APPLICATION ====================
    APP_NAME: str = "WasteWise API"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "AI-Powered Waste Sorting Assistant"
    DEBUG: bool = Field(default=False, env="DEBUG")
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    
    # ==================== API CONFIGURATION ====================
    API_V1_PREFIX: str = "/api/v1"
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30  # 30 days
    
    # ==================== CORS SETTINGS ====================
    BACKEND_CORS_ORIGINS: List[str] = Field(
    default=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "https://wastewise-1-99l2.onrender.com",  # ← Add your frontend URL
    ],
    env="BACKEND_CORS_ORIGINS"
    )
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v. split(",")]
        return v
    
    # ==================== GOOGLE GEMINI AI ====================
    GEMINI_API_KEY: str = Field(..., env="GEMINI_API_KEY")
    GEMINI_MODEL: str = Field(
        default="gemini-2.5-flash",
        env="GEMINI_MODEL"
    )
    GEMINI_TEMPERATURE: float = Field(default=0.4, env="GEMINI_TEMPERATURE")
    GEMINI_MAX_TOKENS: int = Field(default=2048, env="GEMINI_MAX_TOKENS")
    GEMINI_TIMEOUT: int = Field(default=30, env="GEMINI_TIMEOUT")
    
    # ==================== FIREBASE ====================
    FIREBASE_CREDENTIALS_PATH: str = Field(
        default=str(BASE_DIR / "firebase-credentials.json"),
        env="FIREBASE_CREDENTIALS_PATH"
    )
    FIREBASE_DATABASE_URL: Optional[str] = Field(
        default=None,
        env="FIREBASE_DATABASE_URL"
    )
    FIREBASE_STORAGE_BUCKET: Optional[str] = Field(
        default=None,
        env="FIREBASE_STORAGE_BUCKET"
    )
    
    # ==================== FILE UPLOAD ====================
    MAX_UPLOAD_SIZE: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        env="MAX_UPLOAD_SIZE"
    )
    ALLOWED_IMAGE_TYPES: List[str] = Field(
        default=["image/jpeg", "image/png", "image/jpg", "image/webp"],
        env="ALLOWED_IMAGE_TYPES"
    )
    UPLOAD_DIR: str = Field(
        default=str(BASE_DIR / "uploads"),
        env="UPLOAD_DIR"
    )
    
    # ==================== WASTE CATEGORIES ====================
    WASTE_CATEGORIES: List[str] = Field(
        default=[
            "Recyclable Plastic",
            "Paper & Cardboard",
            "Organic/Compost",
            "Hazardous Waste",
            "Non-Recyclable",
            "Metal & Glass",
            "E-Waste",
            "Unknown"
        ],
        env="WASTE_CATEGORIES"
    )
    
    # ==================== GAMIFICATION ====================
    # Points system
    POINTS_FIRST_SCAN: int = 100
    POINTS_CORRECT_DISPOSAL: int = 50
    POINTS_DAILY_LOGIN: int = 10
    POINTS_WEEKLY_STREAK: int = 200
    POINTS_REFERRAL: int = 150
    
    # Level thresholds
    LEVEL_THRESHOLDS: dict = {
        1: 0,        # Newbie
        2: 200,      # Recycler
        3: 500,      # Eco Warrior
        4: 1000,     # Green Champion
        5: 2000,     # Planet Protector
        6: 5000,     # Sustainability Hero
        7: 10000,    # Earth Guardian
    }
    
    # ==================== RATE LIMITING ====================
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    RATE_LIMIT_SCAN_PER_HOUR: int = Field(default=50, env="RATE_LIMIT_SCAN_PER_HOUR")
    
    # ==================== LOGGING ====================
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FILE: str = Field(
        default=str(BASE_DIR / "logs" / "app. log"),
        env="LOG_FILE"
    )
    
    # ==================== DATABASE (Optional SQL) ====================
    DATABASE_URL: Optional[str] = Field(default=None, env="DATABASE_URL")
    
    # ==================== EMAIL (Future Feature) ====================
    SMTP_HOST: Optional[str] = Field(default=None, env="SMTP_HOST")
    SMTP_PORT: Optional[int] = Field(default=587, env="SMTP_PORT")
    SMTP_USER: Optional[str] = Field(default=None, env="SMTP_USER")
    SMTP_PASSWORD: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    EMAILS_FROM_EMAIL: Optional[str] = Field(default=None, env="EMAILS_FROM_EMAIL")
    EMAILS_FROM_NAME: Optional[str] = Field(default="WasteWise", env="EMAILS_FROM_NAME")
    
    # ==================== THIRD-PARTY APIS (Future) ====================
    RECYCLING_CENTER_API_KEY: Optional[str] = Field(
        default=None,
        env="RECYCLING_CENTER_API_KEY"
    )
    
    # ==================== VALIDATORS ====================
    @validator("SECRET_KEY")
    def validate_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v
    
    @validator("ENVIRONMENT")
    def validate_environment(cls, v):
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {allowed}")
        return v
    
    @validator("UPLOAD_DIR")
    def create_upload_dir(cls, v):
        Path(v).mkdir(parents=True, exist_ok=True)
        return v
    
    # ==================== COMPUTED PROPERTIES ====================
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"
    
    @property
    def is_development(self) -> bool:
        return self. ENVIRONMENT == "development"
    
    @property
    def fastapi_kwargs(self) -> dict:
        """FastAPI application configuration"""
        return {
            "title": self.APP_NAME,
            "version": self.APP_VERSION,
            "description": self.APP_DESCRIPTION,
            "debug": self.DEBUG,
            "docs_url": "/docs" if not self.is_production else None,
            "redoc_url": "/redoc" if not self.is_production else None,
        }
    
    # ==================== CONFIG ====================
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance
    Use this function to access settings throughout the app
    """
    return Settings()


# Convenience instance for direct import
settings = get_settings()


# ==================== WASTE DISPOSAL GUIDELINES ====================
WASTE_DISPOSAL_GUIDES = {
    "Recyclable Plastic": {
        "bin_color": "BLUE",
        "instructions": [
            "Remove caps and labels if possible",
            "Rinse clean of food residue",
            "Flatten bottles to save space",
            "Place in blue recycling bin"
        ],
        "examples": ["Plastic bottles", "Food containers", "Plastic bags"],
        "co2_saved_per_kg": 1.5,
        "decomposition_time": "450 years"
    },
    "Paper & Cardboard": {
        "bin_color": "BLUE",
        "instructions": [
            "Keep dry and clean",
            "Flatten cardboard boxes",
            "Remove any plastic tape or stickers",
            "Place in blue recycling bin"
        ],
        "examples": ["Newspapers", "Cardboard boxes", "Office paper"],
        "co2_saved_per_kg": 0.9,
        "decomposition_time": "2-6 weeks"
    },
    "Organic/Compost": {
        "bin_color": "GREEN",
        "instructions": [
            "Remove any plastic or packaging",
            "Can mix with yard waste",
            "Keep in green compost bin",
            "Avoid meat and dairy (for home composting)"
        ],
        "examples": ["Food scraps", "Fruit peels", "Coffee grounds"],
        "co2_saved_per_kg": 0.3,
        "decomposition_time": "2-4 weeks"
    },
    "Hazardous Waste": {
        "bin_color": "RED",
        "instructions": [
            "DO NOT mix with regular trash",
            "Store safely until drop-off",
            "Take to hazardous waste facility",
            "Follow local regulations"
        ],
        "examples": ["Batteries", "Paint", "Chemicals", "Fluorescent bulbs"],
        "co2_saved_per_kg": 0.0,
        "decomposition_time": "Never decomposes safely"
    },
    "Metal & Glass": {
        "bin_color": "BLUE",
        "instructions": [
            "Rinse containers clean",
            "Remove lids and caps",
            "Can mix metals and glass",
            "Place in blue recycling bin"
        ],
        "examples": ["Aluminum cans", "Steel cans", "Glass bottles"],
        "co2_saved_per_kg": 2.1,
        "decomposition_time": "Glass: 1M years, Metal: 50-200 years"
    },
    "E-Waste": {
        "bin_color": "SPECIAL",
        "instructions": [
            "Remove batteries if possible",
            "Wipe personal data from devices",
            "Take to e-waste collection center",
            "Check for manufacturer take-back programs"
        ],
        "examples": ["Old phones", "Computers", "Cables", "Appliances"],
        "co2_saved_per_kg": 1.8,
        "decomposition_time": "Never decomposes, toxic materials"
    },
    "Non-Recyclable": {
        "bin_color": "BLACK/GREY",
        "instructions": [
            "Place in general waste bin",
            "Seal in bag if contaminated",
            "Consider reducing usage of these items",
            "Check if alternative disposal exists"
        ],
        "examples": ["Styrofoam", "Dirty plastics", "Mixed materials"],
        "co2_saved_per_kg": 0.0,
        "decomposition_time": "Varies, often hundreds of years"
    }
  }
