"""
Firebase Database Configuration
Handles Firestore and Firebase Admin SDK initialization
"""

import firebase_admin
from firebase_admin import credentials, firestore, storage
from typing import Optional
import logging
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)

# Global Firebase instances
_firebase_app: Optional[firebase_admin.App] = None
_firestore_client: Optional[firestore.Client] = None
_storage_bucket = None


def initialize_firebase() -> firebase_admin.App:
    """
    Initialize Firebase Admin SDK
    
    Returns:
        Firebase app instance
        
    Raises:
        Exception: If initialization fails
    """
    global _firebase_app, _firestore_client, _storage_bucket
    
    if _firebase_app is not None:
        logger.info("Firebase already initialized")
        return _firebase_app
    
    try:
        # Check if credentials file exists
        cred_path = Path(settings. FIREBASE_CREDENTIALS_PATH)
        
        if not cred_path. exists():
            logger.warning(f"Firebase credentials not found at {cred_path}")
            logger.warning("Firebase features will be disabled")
            return None
        
        # Initialize with credentials
        cred = credentials. Certificate(str(cred_path))
        
        _firebase_app = firebase_admin.initialize_app(cred, {
            'storageBucket': settings.FIREBASE_STORAGE_BUCKET
        })
        
        # Initialize Firestore
        _firestore_client = firestore.client()
        
        # Initialize Storage (if bucket specified)
        if settings.FIREBASE_STORAGE_BUCKET:
            _storage_bucket = storage. bucket()
        
        logger.info("✅ Firebase initialized successfully")
        
        return _firebase_app
        
    except Exception as e:
        logger.error(f"❌ Firebase initialization failed: {str(e)}")
        raise


def get_firestore_client() -> Optional[firestore.Client]:
    """
    Get Firestore client instance
    
    Returns:
        Firestore client or None if not initialized
    """
    if _firestore_client is None:
        initialize_firebase()
    
    return _firestore_client


def get_storage_bucket() -> Optional[object]:
    """
    Get Firebase Storage bucket
    
    Returns:
        Storage bucket or None if not initialized
    """
    if _storage_bucket is None:
        initialize_firebase()
    
    return _storage_bucket


def close_firebase():
    """
    Close Firebase connections
    """
    global _firebase_app, _firestore_client, _storage_bucket
    
    try:
        if _firebase_app:
            firebase_admin.delete_app(_firebase_app)
            _firebase_app = None
            _firestore_client = None
            _storage_bucket = None
            logger.info("✅ Firebase connection closed")
    except Exception as e:
        logger. error(f"❌ Error closing Firebase: {str(e)}")


# ==================== FIRESTORE HELPERS ====================

class FirestoreCollections:
    """Firestore collection names"""
    USERS = "users"
    WASTE_SCANS = "waste_scans"
    ACHIEVEMENTS = "achievements"
    LEADERBOARD = "leaderboard"
    FEEDBACK = "feedback"


def get_collection(collection_name: str):
    """
    Get Firestore collection reference
    
    Args:
        collection_name: Name of collection
        
    Returns:
        Collection reference
    """
    db = get_firestore_client()
    if db is None:
        raise Exception("Firestore not initialized")
    
    return db. collection(collection_name)


async def create_document(collection: str, document_id: str, data: dict) -> bool:
    """
    Create or update a document in Firestore
    
    Args:
        collection: Collection name
        document_id: Document ID
        data: Document data
        
    Returns:
        True if successful
    """
    try:
        db = get_firestore_client()
        db.collection(collection).document(document_id).set(data)
        return True
    except Exception as e:
        logger.error(f"Error creating document: {str(e)}")
        return False


async def get_document(collection: str, document_id: str) -> Optional[dict]:
    """
    Get a document from Firestore
    
    Args:
        collection: Collection name
        document_id: Document ID
        
    Returns:
        Document data or None
    """
    try:
        db = get_firestore_client()
        doc = db.collection(collection).document(document_id). get()
        return doc.to_dict() if doc.exists else None
    except Exception as e:
        logger.error(f"Error getting document: {str(e)}")
        return None
