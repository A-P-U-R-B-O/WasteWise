"""
Image Processing Utilities
Handles image upload, validation, conversion, and optimization
"""

import io
import base64
import hashlib
import mimetypes
from typing import Tuple, Optional, Dict, Any
from pathlib import Path
from datetime import datetime
import logging

from PIL import Image, ImageOps, ExifTags
import magic  # python-magic for file type detection

from app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)


class ImageProcessor:
    """
    Handles all image processing operations including:
    - Validation
    - Format conversion
    - Compression
    - Metadata extraction
    - Storage preparation
    """
    
    def __init__(self):
        """Initialize image processor with configuration"""
        self.max_size = settings.MAX_UPLOAD_SIZE
        self.allowed_types = settings.ALLOWED_IMAGE_TYPES
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Image size constraints
        self.max_dimension = 4096  # Maximum width or height
        self.optimal_dimension = 1024  # Optimal for AI processing
        self.thumbnail_size = (300, 300)  # For thumbnails
        
        logger.info("✅ ImageProcessor initialized")
    
    def validate_image(self, file_data: bytes, filename: str) -> Tuple[bool, Optional[str]]:
        """
        Validate image file
        
        Args:
            file_data: Raw file bytes
            filename: Original filename
            
        Returns:
            Tuple of (is_valid, error_message)
            
        Example:
            >>> processor = ImageProcessor()
            >>> is_valid, error = processor.validate_image(image_bytes, "photo.jpg")
            >>> if not is_valid:
            ...     print(f"Error: {error}")
        """
        # Check file size
        if len(file_data) > self.max_size:
            max_mb = self.max_size / (1024 * 1024)
            return False, f"File too large. Maximum size is {max_mb:.1f}MB"
        
        if len(file_data) == 0:
            return False, "File is empty"
        
        # Check MIME type using python-magic (more reliable than extension)
        try:
            mime = magic.from_buffer(file_data, mime=True)
            if mime not in self.allowed_types:
                allowed = ", ".join([t.split('/')[1]. upper() for t in self.allowed_types])
                return False, f"Invalid file type. Allowed types: {allowed}"
        except Exception as e:
            logger.warning(f"⚠️ MIME type detection failed: {str(e)}")
            # Fallback to extension check
            ext = Path(filename).suffix.lower()
            if ext not in ['.jpg', '.jpeg', '.png', '.webp']:
                return False, "Invalid file type"
        
        # Try to open image with PIL
        try:
            image = Image.open(io. BytesIO(file_data))
            image.verify()  # Verify it's a valid image
            
            # Check dimensions
            width, height = image.size
            if width < 50 or height < 50:
                return False, "Image too small (minimum 50x50 pixels)"
            
            if width > self.max_dimension or height > self.max_dimension:
                return False, f"Image too large (maximum {self.max_dimension}x{self.max_dimension} pixels)"
            
        except Exception as e:
            return False, f"Invalid or corrupted image file: {str(e)}"
        
        return True, None
    
    def process_image(
        self, 
        file_data: bytes, 
        filename: str,
        optimize: bool = True,
        create_thumbnail: bool = True
    ) -> Dict[str, Any]:
        """
        Process image: validate, optimize, extract metadata
        
        Args:
            file_data: Raw image bytes
            filename: Original filename
            optimize: Whether to optimize/compress image
            create_thumbnail: Whether to create thumbnail
            
        Returns:
            Dictionary containing processed image data and metadata
            
        Raises:
            ValueError: If image validation fails
            
        Example:
            >>> processor = ImageProcessor()
            >>> result = processor.process_image(image_bytes, "photo.jpg")
            >>> print(result["optimized_size"])
        """
        # Validate first
        is_valid, error = self.validate_image(file_data, filename)
        if not is_valid:
            raise ValueError(error)
        
        logger.info(f"📸 Processing image: {filename}")
        
        # Open image
        image = Image.open(io.BytesIO(file_data))
        
        # Fix orientation based on EXIF data
        image = self._fix_orientation(image)
        
        # Extract metadata
        metadata = self._extract_metadata(image, filename, len(file_data))
        
        # Optimize image if requested
        optimized_data = file_data
        if optimize:
            optimized_image, optimized_data = self._optimize_image(image)
            metadata["optimized_size"] = len(optimized_data)
            metadata["compression_ratio"] = len(file_data) / len(optimized_data)
        
        # Create thumbnail if requested
        thumbnail_data = None
        if create_thumbnail:
            thumbnail_data = self._create_thumbnail(image)
            metadata["thumbnail_size"] = len(thumbnail_data) if thumbnail_data else 0
        
        # Convert to base64 for API transmission
        base64_image = self. to_base64(optimized_data)
        base64_thumbnail = self.to_base64(thumbnail_data) if thumbnail_data else None
        
        # Generate unique hash for the image
        image_hash = self._generate_hash(optimized_data)
        
        logger.info(f"✅ Image processed: {metadata['format']} | "
                   f"Original: {metadata['original_size']//1024}KB | "
                   f"Optimized: {metadata. get('optimized_size', 0)//1024}KB")
        
        return {
            "metadata": metadata,
            "original_data": file_data,
            "optimized_data": optimized_data,
            "thumbnail_data": thumbnail_data,
            "base64_image": base64_image,
            "base64_thumbnail": base64_thumbnail,
            "image_hash": image_hash,
            "filename": filename
        }
    
    def _fix_orientation(self, image: Image.Image) -> Image.Image:
        """
        Fix image orientation based on EXIF data
        (Important for photos taken on mobile devices)
        
        Args:
            image: PIL Image object
            
        Returns:
            Corrected PIL Image object
        """
        try:
            # Get EXIF data
            exif = image._getexif()
            if exif is None:
                return image
            
            # Find orientation tag
            orientation_key = None
            for key in ExifTags.TAGS. keys():
                if ExifTags.TAGS[key] == 'Orientation':
                    orientation_key = key
                    break
            
            if orientation_key is None:
                return image
            
            orientation = exif.get(orientation_key)
            
            # Rotate based on orientation
            if orientation == 3:
                image = image.rotate(180, expand=True)
            elif orientation == 6:
                image = image.rotate(270, expand=True)
            elif orientation == 8:
                image = image.rotate(90, expand=True)
            
            logger.info(f"🔄 Fixed image orientation: {orientation}")
            
        except (AttributeError, KeyError, IndexError):
            # No EXIF data or orientation tag
            pass
        
        return image
    
    def _extract_metadata(self, image: Image.Image, filename: str, file_size: int) -> Dict[str, Any]:
        """
        Extract metadata from image
        
        Args:
            image: PIL Image object
            filename: Original filename
            file_size: File size in bytes
            
        Returns:
            Metadata dictionary
        """
        width, height = image.size
        
        metadata = {
            "filename": filename,
            "format": image.format or "UNKNOWN",
            "mode": image.mode,
            "width": width,
            "height": height,
            "aspect_ratio": round(width / height, 2) if height > 0 else 0,
            "megapixels": round((width * height) / 1_000_000, 2),
            "original_size": file_size,
            "size_mb": round(file_size / (1024 * 1024), 2),
            "has_transparency": image.mode in ('RGBA', 'LA', 'P'),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Extract EXIF data if available
        try:
            exif = image._getexif()
            if exif:
                metadata["exif"] = {
                    ExifTags. TAGS. get(key, key): value
                    for key, value in exif.items()
                    if key in ExifTags. TAGS and isinstance(value, (str, int, float))
                }
        except:
            metadata["exif"] = {}
        
        return metadata
    
    def _optimize_image(self, image: Image.Image) -> Tuple[Image.Image, bytes]:
        """
        Optimize image for storage and processing
        
        Args:
            image: PIL Image object
            
        Returns:
            Tuple of (optimized_image, optimized_bytes)
        """
        # Convert to RGB if necessary (remove alpha channel)
        if image.mode in ('RGBA', 'LA', 'P'):
            # Create white background
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Resize if too large
        if max(image.size) > self. optimal_dimension:
            ratio = self.optimal_dimension / max(image.size)
            new_size = tuple(int(dim * ratio) for dim in image.size)
            image = image.resize(new_size, Image.Resampling.LANCZOS)
            logger.info(f"📐 Resized image to: {new_size}")
        
        # Compress and save to bytes
        output = io.BytesIO()
        image.save(
            output,
            format='JPEG',
            quality=85,  # Good balance between quality and size
            optimize=True,
            progressive=True  # Progressive JPEG for better web loading
        )
        optimized_data = output.getvalue()
        
        return image, optimized_data
    
    def _create_thumbnail(self, image: Image.Image) -> bytes:
        """
        Create thumbnail version of image
        
        Args:
            image: PIL Image object
            
        Returns:
            Thumbnail image as bytes
        """
        # Create copy for thumbnail
        thumb = image.copy()
        
        # Convert to RGB if needed
        if thumb.mode != 'RGB':
            thumb = thumb.convert('RGB')
        
        # Create thumbnail (maintains aspect ratio)
        thumb. thumbnail(self.thumbnail_size, Image.Resampling. LANCZOS)
        
        # Save to bytes
        output = io.BytesIO()
        thumb.save(
            output,
            format='JPEG',
            quality=80,
            optimize=True
        )
        
        return output.getvalue()
    
    def _generate_hash(self, data: bytes) -> str:
        """
        Generate SHA-256 hash of image data
        Useful for detecting duplicate uploads
        
        Args:
            data: Image bytes
            
        Returns:
            Hexadecimal hash string
        """
        return hashlib.sha256(data).hexdigest()
    
    def to_base64(self, image_data: bytes) -> str:
        """
        Convert image bytes to base64 string
        
        Args:
            image_data: Image bytes
            
        Returns:
            Base64 encoded string
            
        Example:
            >>> processor = ImageProcessor()
            >>> b64 = processor.to_base64(image_bytes)
            >>> # Can be used in HTML: <img src="data:image/jpeg;base64,{b64}">
        """
        return base64.b64encode(image_data).decode('utf-8')
    
    def from_base64(self, base64_string: str) -> bytes:
        """
        Convert base64 string to image bytes
        
        Args:
            base64_string: Base64 encoded image string
            
        Returns:
            Image bytes
            
        Raises:
            ValueError: If base64 string is invalid
        """
        try:
            # Remove data URL prefix if present
            if ',' in base64_string:
                base64_string = base64_string.split(',', 1)[1]
            
            return base64.b64decode(base64_string)
        except Exception as e:
            raise ValueError(f"Invalid base64 string: {str(e)}")
    
    def save_image(
        self, 
        image_data: bytes, 
        filename: Optional[str] = None,
        subfolder: str = ""
    ) -> Path:
        """
        Save image to disk
        
        Args:
            image_data: Image bytes to save
            filename: Optional custom filename (auto-generated if None)
            subfolder: Optional subfolder within upload directory
            
        Returns:
            Path to saved file
            
        Example:
            >>> processor = ImageProcessor()
            >>> path = processor. save_image(image_bytes, subfolder="scans/2024-01")
            >>> print(f"Saved to: {path}")
        """
        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.utcnow(). strftime("%Y%m%d_%H%M%S")
            image_hash = self._generate_hash(image_data)[:8]
            filename = f"{timestamp}_{image_hash}.jpg"
        
        # Create subfolder if needed
        save_dir = self.upload_dir / subfolder
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # Full path
        filepath = save_dir / filename
        
        # Save file
        with open(filepath, 'wb') as f:
            f.write(image_data)
        
        logger.info(f"💾 Saved image to: {filepath}")
        
        return filepath
    
    def delete_image(self, filepath: Path) -> bool:
        """
        Delete image file from disk
        
        Args:
            filepath: Path to file to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            if filepath. exists():
                filepath.unlink()
                logger.info(f"🗑️ Deleted image: {filepath}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Failed to delete image: {str(e)}")
            return False
    
    def get_image_info(self, file_data: bytes) -> Dict[str, Any]:
        """
        Quick method to get basic image information without full processing
        
        Args:
            file_data: Image bytes
            
        Returns:
            Basic image information dictionary
        """
        try:
            image = Image. open(io.BytesIO(file_data))
            return {
                "valid": True,
                "format": image.format,
                "mode": image.mode,
                "size": image.size,
                "width": image.size[0],
                "height": image.size[1],
                "file_size": len(file_data)
            }
        except Exception as e:
            return {
                "valid": False,
                "error": str(e)
            }


# ==================== SINGLETON INSTANCE ====================
_image_processor_instance: Optional[ImageProcessor] = None


def get_image_processor() -> ImageProcessor:
    """
    Get singleton instance of ImageProcessor
    
    Returns:
        ImageProcessor instance
        
    Example:
        >>> processor = get_image_processor()
        >>> result = processor.process_image(image_bytes, "photo.jpg")
    """
    global _image_processor_instance
    
    if _image_processor_instance is None:
        _image_processor_instance = ImageProcessor()
    
    return _image_processor_instance


# ==================== HELPER FUNCTIONS ====================

def validate_uploaded_file(file_data: bytes, filename: str) -> Tuple[bool, Optional[str]]:
    """
    Quick validation helper
    
    Args:
        file_data: File bytes
        filename: Filename
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    processor = get_image_processor()
    return processor.validate_image(file_data, filename)


def process_uploaded_image(file_data: bytes, filename: str) -> Dict[str, Any]:
    """
    Quick processing helper
    
    Args:
        file_data: File bytes
        filename: Filename
        
    Returns:
        Processed image data dictionary
    """
    processor = get_image_processor()
    return processor.process_image(file_data, filename)


def create_data_url(image_data: bytes, mime_type: str = "image/jpeg") -> str:
    """
    Create data URL from image bytes
    Can be used directly in HTML <img> tags
    
    Args:
        image_data: Image bytes
        mime_type: MIME type of image
        
    Returns:
        Data URL string
        
    Example:
        >>> data_url = create_data_url(image_bytes)
        >>> # Use in HTML: <img src="{data_url}">
    """
    processor = get_image_processor()
    b64 = processor.to_base64(image_data)
    return f"data:{mime_type};base64,{b64}"


def estimate_upload_time(file_size: int, bandwidth_mbps: float = 10.0) -> float:
    """
    Estimate upload time for an image
    
    Args:
        file_size: File size in bytes
        bandwidth_mbps: Upload bandwidth in Mbps
        
    Returns:
        Estimated time in seconds
    """
    # Convert to megabits
    file_size_mb = (file_size * 8) / (1024 * 1024)
    return file_size_mb / bandwidth_mbps


def get_optimal_image_format(has_transparency: bool = False) -> str:
    """
    Get recommended image format based on requirements
    
    Args:
        has_transparency: Whether image needs transparency
        
    Returns:
        Recommended format ('JPEG', 'PNG', or 'WEBP')
    """
    if has_transparency:
        return 'PNG'  # PNG supports transparency
    return 'JPEG'  # JPEG for smaller file size


def batch_process_images(
    image_files: list[Tuple[bytes, str]],
    max_workers: int = 4
) -> list[Dict[str, Any]]:
    """
    Process multiple images (can be extended for parallel processing)
    
    Args:
        image_files: List of (file_data, filename) tuples
        max_workers: Maximum parallel workers (for future implementation)
        
    Returns:
        List of processed image results
    """
    processor = get_image_processor()
    results = []
    
    for file_data, filename in image_files:
        try:
            result = processor.process_image(file_data, filename)
            results.append(result)
        except Exception as e:
            results.append({
                "error": True,
                "filename": filename,
                "error_message": str(e)
            })
    
    return results
