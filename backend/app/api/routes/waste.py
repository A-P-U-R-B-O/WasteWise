"""
Waste Identification API Routes
Handles waste scanning, identification, and disposal guidance
"""

from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Request, Form
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from datetime import datetime
import logging

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings
from app.services.gemini_service import get_gemini_service
from app.utils.image_processor import get_image_processor, validate_uploaded_file
from app.core.database import get_firestore_client, FirestoreCollections

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


# ==================== PYDANTIC MODELS ====================

class WasteScanResponse(BaseModel):
    """Response model for waste scan"""
    success: bool = True
    scan_id: Optional[str] = None
    item_name: str
    category: str
    confidence: float = Field(ge=0.0, le=1.0)
    subcategory: Optional[str] = None
    recyclable: bool
    disposal_steps: List[str]
    bin_color: str
    environmental_impact: Dict[str, Any]
    additional_tips: Optional[List[str]] = []
    warnings: Optional[List[str]] = []
    alternatives: Optional[str] = None
    points_earned: int = 0
    processing_time_seconds: float
    timestamp: str
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "scan_id": "scan_20241204_abc123",
                "item_name": "Plastic Water Bottle",
                "category": "Recyclable Plastic",
                "confidence": 0.95,
                "subcategory": "PET Plastic",
                "recyclable": True,
                "disposal_steps": [
                    "Remove cap and label",
                    "Rinse bottle clean",
                    "Place in blue recycling bin"
                ],
                "bin_color": "BLUE",
                "environmental_impact": {
                    "co2_saved_kg": 1.5,
                    "decomposition_time": "450 years",
                    "recycling_potential": "Can be recycled 7+ times"
                },
                "points_earned": 50,
                "processing_time_seconds": 2.34,
                "timestamp": "2024-12-04T10:30:00Z"
            }
        }


class WasteScanRequest(BaseModel):
    """Request model for waste scan with base64 image"""
    image_base64: str = Field(..., description="Base64 encoded image")
    user_id: Optional[str] = Field(None, description="User ID for tracking")
    location: Optional[Dict[str, float]] = Field(None, description="GPS coordinates")
    
    @validator('image_base64')
    def validate_base64(cls, v):
        if not v or len(v) < 100:
            raise ValueError("Invalid base64 image data")
        return v


class EducationalContentResponse(BaseModel):
    """Response model for educational content"""
    success: bool = True
    category: str
    bin_color: str
    instructions: List[str]
    examples: List[str]
    co2_saved_per_kg: float
    decomposition_time: str
    facts: Optional[List[str]] = []
    global_impact: Optional[str] = None
    did_you_know: Optional[str] = None


class WasteCategoriesResponse(BaseModel):
    """Response model for waste categories"""
    success: bool = True
    categories: List[str]
    total: int


# ==================== HELPER FUNCTIONS ====================

async def save_scan_to_database(
    scan_data: Dict[str, Any],
    user_id: Optional[str] = None
) -> str:
    """
    Save scan result to Firestore
    
    Args:
        scan_data: Scan result data
        user_id: Optional user ID
        
    Returns:
        Scan document ID
    """
    try:
        db = get_firestore_client()
        if db is None:
            logger.warning("Firestore not available, skipping database save")
            return "scan_" + datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        # Generate scan ID
        scan_id = f"scan_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{user_id or 'anonymous'}"
        
        # Prepare document
        document = {
            "scan_id": scan_id,
            "user_id": user_id or "anonymous",
            "item_name": scan_data.get("item_name"),
            "category": scan_data.get("category"),
            "confidence": scan_data.get("confidence"),
            "recyclable": scan_data.get("recyclable"),
            "points_earned": scan_data.get("points_earned", 0),
            "timestamp": datetime.utcnow(). isoformat(),
            "processing_time": scan_data.get("processing_time_seconds"),
            "location": scan_data.get("location"),
            "image_hash": scan_data.get("image_hash")
        }
        
        # Save to Firestore
        db.collection(FirestoreCollections.WASTE_SCANS). document(scan_id).set(document)
        
        # Update user stats if user_id provided
        if user_id:
            await update_user_stats(user_id, scan_data)
        
        logger.info(f"✅ Scan saved to database: {scan_id}")
        return scan_id
        
    except Exception as e:
        logger.error(f"❌ Failed to save scan to database: {str(e)}")
        return "scan_" + datetime.utcnow().strftime("%Y%m%d_%H%M%S")


async def update_user_stats(user_id: str, scan_data: Dict[str, Any]):
    """
    Update user statistics after scan
    
    Args:
        user_id: User ID
        scan_data: Scan result data
    """
    try:
        db = get_firestore_client()
        if db is None:
            return
        
        user_ref = db.collection(FirestoreCollections.USERS).document(user_id)
        user_doc = user_ref.get()
        
        if user_doc.exists:
            # Update existing user
            user_data = user_doc.to_dict()
            
            # Increment counters
            user_ref.update({
                "total_scans": user_data. get("total_scans", 0) + 1,
                "total_points": user_data.get("total_points", 0) + scan_data.get("points_earned", 0),
                "co2_saved_kg": user_data.get("co2_saved_kg", 0.0) + scan_data.get("environmental_impact", {}).get("co2_saved_kg", 0.0),
                "last_scan_timestamp": datetime.utcnow(). isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            })
            
            logger.info(f"✅ Updated stats for user: {user_id}")
        else:
            # Create new user stats
            user_ref.set({
                "user_id": user_id,
                "total_scans": 1,
                "total_points": scan_data.get("points_earned", 0),
                "co2_saved_kg": scan_data.get("environmental_impact", {}).get("co2_saved_kg", 0.0),
                "level": 1,
                "created_at": datetime.utcnow().isoformat(),
                "last_scan_timestamp": datetime.utcnow().isoformat()
            })
            
            logger.info(f"✅ Created new user stats: {user_id}")
            
    except Exception as e:
        logger.error(f"❌ Failed to update user stats: {str(e)}")


# ==================== ROUTES ====================

@router.post("/scan", response_model=WasteScanResponse)
@limiter.limit(f"{settings. RATE_LIMIT_SCAN_PER_HOUR}/hour")
async def scan_waste_image(
    request: Request,
    file: UploadFile = File(... , description="Image file to scan"),
    user_id: Optional[str] = Form(None, description="User ID for tracking")
):
    """
    **Scan waste item from uploaded image**
    
    Upload an image of a waste item to identify its type and get disposal instructions.
    
    - **file**: Image file (JPEG, PNG, WebP)
    - **user_id**: Optional user ID for tracking and points
    
    Returns:
    - Waste item identification
    - Disposal instructions
    - Environmental impact
    - Points earned
    """
    try:
        logger.info(f"📸 Received waste scan request from {request.client.host if request.client else 'unknown'}")
        
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Please upload an image file (JPEG, PNG, WebP)"
            )
        
        # Read file data
        file_data = await file.read()
        
        if len(file_data) == 0:
            raise HTTPException(status_code=400, detail="Empty file uploaded")
        
        # Validate image
        image_processor = get_image_processor()
        is_valid, error_message = validate_uploaded_file(file_data, file.filename)
        
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_message)
        
        logger.info(f"✅ Image validated: {file.filename} ({len(file_data) / 1024:.1f} KB)")
        
        # Process image
        processed = image_processor.process_image(file_data, file.filename)
        
        # Identify waste using Gemini
        gemini_service = get_gemini_service()
        result = await gemini_service.identify_waste(processed['optimized_data'])
        
        # Check for errors
        if result.get("error"):
            raise HTTPException(
                status_code=500,
                detail=f"Waste identification failed: {result.get('error_message', 'Unknown error')}"
            )
        
        # Add image hash
        result["image_hash"] = processed["image_hash"]
        
        # Save to database
        scan_id = await save_scan_to_database(result, user_id)
        result["scan_id"] = scan_id
        
        # Add timestamp
        result["timestamp"] = datetime.utcnow().isoformat()
        
        logger. info(f"✅ Scan completed: {result['item_name']} | Confidence: {result['confidence']:.1%} | Points: {result. get('points_earned', 0)}")
        
        return WasteScanResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Scan failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred during waste identification: {str(e)}"
        )


@router.post("/scan/base64", response_model=WasteScanResponse)
@limiter.limit(f"{settings. RATE_LIMIT_SCAN_PER_HOUR}/hour")
async def scan_waste_base64(
    request: Request,
    scan_request: WasteScanRequest
):
    """
    **Scan waste item from base64 encoded image**
    
    Alternative endpoint for scanning using base64 encoded images.
    Useful for web applications that capture images directly in the browser.
    
    - **image_base64**: Base64 encoded image data
    - **user_id**: Optional user ID for tracking
    - **location**: Optional GPS coordinates
    
    Returns same data as /scan endpoint
    """
    try:
        logger.info(f"📸 Received base64 scan request")
        
        # Decode base64 image
        image_processor = get_image_processor()
        
        try:
            file_data = image_processor.from_base64(scan_request. image_base64)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        
        # Validate image
        is_valid, error_message = validate_uploaded_file(file_data, "scan. jpg")
        
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_message)
        
        # Process image
        processed = image_processor. process_image(file_data, "scan.jpg")
        
        # Identify waste
        gemini_service = get_gemini_service()
        result = await gemini_service.identify_waste(processed['optimized_data'])
        
        if result.get("error"):
            raise HTTPException(status_code=500, detail=result.get('error_message'))
        
        # Add metadata
        result["image_hash"] = processed["image_hash"]
        result["location"] = scan_request.location
        
        # Save to database
        scan_id = await save_scan_to_database(result, scan_request.user_id)
        result["scan_id"] = scan_id
        result["timestamp"] = datetime.utcnow().isoformat()
        
        logger.info(f"✅ Base64 scan completed: {result['item_name']}")
        
        return WasteScanResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Base64 scan failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories", response_model=WasteCategoriesResponse)
async def get_waste_categories():
    """
    **Get all supported waste categories**
    
    Returns a list of all waste categories that the AI can identify.
    """
    return WasteCategoriesResponse(
        categories=settings.WASTE_CATEGORIES,
        total=len(settings. WASTE_CATEGORIES)
    )


@router.get("/education/{category}", response_model=EducationalContentResponse)
async def get_educational_content(category: str):
    """
    **Get educational content about a waste category**
    
    Returns detailed information, tips, and facts about a specific waste category.
    
    - **category**: Waste category name (e.g., "Recyclable Plastic")
    """
    try:
        # Validate category
        if category not in settings.WASTE_CATEGORIES:
            raise HTTPException(
                status_code=404,
                detail=f"Category '{category}' not found. Use /categories to see valid categories."
            )
        
        # Get educational content
        gemini_service = get_gemini_service()
        content = await gemini_service.get_educational_content(category)
        
        if content. get("error"):
            raise HTTPException(status_code=404, detail="Educational content not found")
        
        return EducationalContentResponse(**content)
        
    except HTTPException:
        raise
    except Exception as e:
        logger. error(f"❌ Failed to get educational content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{user_id}")
@limiter.limit("30/minute")
async def get_scan_history(
    request: Request,
    user_id: str,
    limit: int = 20,
    offset: int = 0
):
    """
    **Get scan history for a user**
    
    Returns the scanning history for a specific user. 
    
    - **user_id**: User ID
    - **limit**: Number of results to return (max 100)
    - **offset**: Number of results to skip
    """
    try:
        # Validate limit
        if limit > 100:
            limit = 100
        
        db = get_firestore_client()
        if db is None:
            raise HTTPException(
                status_code=503,
                detail="Database service unavailable"
            )
        
        # Query scans
        scans_ref = db.collection(FirestoreCollections.WASTE_SCANS) \
            .where("user_id", "==", user_id) \
            .order_by("timestamp", direction=firestore.Query.DESCENDING) \
            .limit(limit) \
            .offset(offset)
        
        scans = scans_ref.stream()
        
        # Convert to list
        scan_list = []
        for scan in scans:
            scan_data = scan.to_dict()
            scan_data["id"] = scan. id
            scan_list.append(scan_data)
        
        logger.info(f"✅ Retrieved {len(scan_list)} scans for user {user_id}")
        
        return {
            "success": True,
            "user_id": user_id,
            "scans": scan_list,
            "count": len(scan_list),
            "limit": limit,
            "offset": offset
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get scan history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/{user_id}")
async def get_user_stats(user_id: str):
    """
    **Get statistics for a user**
    
    Returns scanning statistics and environmental impact for a user.
    
    - **user_id**: User ID
    """
    try:
        db = get_firestore_client()
        if db is None:
            raise HTTPException(status_code=503, detail="Database service unavailable")
        
        # Get user stats
        user_ref = db.collection(FirestoreCollections.USERS).document(user_id)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            raise HTTPException(status_code=404, detail="User not found")
        
        stats = user_doc.to_dict()
        
        # Calculate level
        total_points = stats.get("total_points", 0)
        level = 1
        for lvl, threshold in sorted(settings.LEVEL_THRESHOLDS.items(), reverse=True):
            if total_points >= threshold:
                level = lvl
                break
        
        stats["level"] = level
        stats["next_level_points"] = None
        
        # Find next level threshold
        for lvl in sorted(settings.LEVEL_THRESHOLDS.keys()):
            if lvl > level:
                stats["next_level_points"] = settings.LEVEL_THRESHOLDS[lvl] - total_points
                break
        
        return {
            "success": True,
            "user_id": user_id,
            "stats": stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger. error(f"❌ Failed to get user stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/scan/{scan_id}")
async def delete_scan(scan_id: str, user_id: str):
    """
    **Delete a scan record**
    
    Delete a specific scan from history.
    
    - **scan_id**: Scan ID to delete
    - **user_id**: User ID (for authorization)
    """
    try:
        db = get_firestore_client()
        if db is None:
            raise HTTPException(status_code=503, detail="Database service unavailable")
        
        # Get scan document
        scan_ref = db. collection(FirestoreCollections. WASTE_SCANS). document(scan_id)
        scan_doc = scan_ref.get()
        
        if not scan_doc.exists:
            raise HTTPException(status_code=404, detail="Scan not found")
        
        scan_data = scan_doc.to_dict()
        
        # Verify ownership
        if scan_data.get("user_id") != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this scan")
        
        # Delete
        scan_ref.delete()
        
        logger.info(f"✅ Deleted scan: {scan_id}")
        
        return {
            "success": True,
            "message": "Scan deleted successfully",
            "scan_id": scan_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to delete scan: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
