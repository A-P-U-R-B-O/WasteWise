"""
Gemini AI Service
Handles all interactions with Google's Gemini AI for waste identification
"""

import google.generativeai as genai
from typing import Dict, Any, Optional, List
import base64
import io
from PIL import Image
import json
import logging
from pathlib import Path
import time

from app.core.config import settings, WASTE_DISPOSAL_GUIDES

# Configure logging
logger = logging.getLogger(__name__)


class GeminiService:
    """
    Service class for interacting with Google Gemini AI
    Handles waste identification and disposal guidance
    """
    
    def __init__(self):
        """Initialize Gemini AI with API key"""
        try:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
            logger.info(f"✅ Gemini AI initialized with model: {settings. GEMINI_MODEL}")
        except Exception as e:
            logger. error(f"❌ Failed to initialize Gemini AI: {str(e)}")
            raise
    
    def _prepare_image(self, image_data: bytes) -> Image.Image:
        """
        Prepare and validate image for Gemini processing
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            PIL Image object
            
        Raises:
            ValueError: If image is invalid or too large
        """
        try:
            # Open image
            image = Image.open(io.BytesIO(image_data))
            
            # Validate image
            if image.size[0] * image.size[1] > 4096 * 4096:
                raise ValueError("Image resolution too high (max 4096x4096)")
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize if too large (optimize for API)
            max_size = 2048
            if max(image.size) > max_size:
                ratio = max_size / max(image.size)
                new_size = tuple(int(dim * ratio) for dim in image.size)
                image = image.resize(new_size, Image.Resampling.LANCZOS)
                logger.info(f"📐 Image resized to: {new_size}")
            
            return image
            
        except Exception as e:
            logger. error(f"❌ Image preparation failed: {str(e)}")
            raise ValueError(f"Invalid image format: {str(e)}")
    
    def _create_waste_identification_prompt(self) -> str:
        """
        Create detailed prompt for waste identification
        
        Returns:
            Structured prompt string
        """
        categories = ", ".join(settings.WASTE_CATEGORIES)
        
        prompt = f"""You are an expert waste management and recycling AI assistant.  Analyze this image and identify the waste item. 

**YOUR TASK:**
1. Identify the primary waste item in the image
2.  Classify it into ONE of these categories: {categories}
3. Provide disposal instructions
4. Calculate environmental impact

**RESPONSE FORMAT (JSON only):**
{{
    "item_name": "specific name of the item (e.g., 'Plastic Water Bottle', 'Banana Peel')",
    "category": "one of: {categories}",
    "confidence": 0.0-1.0 (your confidence in this classification),
    "subcategory": "specific type (e.g., 'PET Plastic', 'Aluminum Can')",
    "recyclable": true/false,
    "disposal_steps": [
        "Step 1: specific instruction",
        "Step 2: specific instruction",
        "Step 3: specific instruction"
    ],
    "bin_color": "recommended bin color (e.g., BLUE, GREEN, BLACK, RED)",
    "environmental_impact": {{
        "co2_saved_kg": 0.0 (if recycled properly),
        "decomposition_time": "time to decompose if sent to landfill",
        "recycling_potential": "can be recycled X times / not recyclable"
    }},
    "additional_tips": [
        "helpful tip 1",
        "helpful tip 2"
    ],
    "warnings": [
        "any warnings or important notes"
    ],
    "alternatives": "suggestion for reducing this type of waste in future"
}}

**IMPORTANT RULES:**
- Be specific: "Plastic PET bottle" not just "plastic"
- If unsure, use category "Unknown" and confidence < 0.5
- Always provide actionable disposal steps
- Consider local recycling standards
- If multiple items visible, identify the most prominent one
- Return ONLY valid JSON, no additional text

Analyze the image now:"""
        
        return prompt
    
    def _parse_gemini_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse and validate Gemini's JSON response
        
        Args:
            response_text: Raw response from Gemini
            
        Returns:
            Parsed and validated waste data dictionary
        """
        try:
            # Try to extract JSON from response
            # Sometimes Gemini adds markdown code blocks
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end]. strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            
            # Parse JSON
            data = json. loads(response_text)
            
            # Validate required fields
            required_fields = ["item_name", "category", "confidence"]
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Validate category
            if data["category"] not in settings.WASTE_CATEGORIES:
                logger.warning(f"⚠️ Unknown category: {data['category']}, defaulting to 'Unknown'")
                data["category"] = "Unknown"
            
            # Ensure confidence is float between 0 and 1
            data["confidence"] = max(0.0, min(1.0, float(data. get("confidence", 0. 5))))
            
            # Add disposal guide from config if available
            if data["category"] in WASTE_DISPOSAL_GUIDES:
                guide = WASTE_DISPOSAL_GUIDES[data["category"]]
                
                # Merge with AI response (AI takes priority for disposal_steps)
                if "disposal_steps" not in data or not data["disposal_steps"]:
                    data["disposal_steps"] = guide["instructions"]
                
                if "bin_color" not in data:
                    data["bin_color"] = guide["bin_color"]
                
                # Enhance environmental impact
                if "environmental_impact" not in data:
                    data["environmental_impact"] = {}
                
                data["environmental_impact"]. setdefault(
                    "co2_saved_kg", 
                    guide["co2_saved_per_kg"]
                )
                data["environmental_impact"].setdefault(
                    "decomposition_time", 
                    guide["decomposition_time"]
                )
                
                # Add examples
                data["examples"] = guide. get("examples", [])
            
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON parsing failed: {str(e)}\nResponse: {response_text}")
            # Return fallback response
            return self._create_fallback_response(response_text)
        except Exception as e:
            logger.error(f"❌ Response parsing failed: {str(e)}")
            return self._create_fallback_response(response_text)
    
    def _create_fallback_response(self, raw_response: str) -> Dict[str, Any]:
        """
        Create fallback response when parsing fails
        
        Args:
            raw_response: Raw text from Gemini
            
        Returns:
            Basic response dictionary
        """
        return {
            "item_name": "Unknown Item",
            "category": "Unknown",
            "confidence": 0.3,
            "subcategory": "Unidentified",
            "recyclable": False,
            "disposal_steps": [
                "Unable to identify waste type clearly",
                "Please retake photo with better lighting",
                "Ensure the item is clearly visible",
                "Consult local waste management guidelines"
            ],
            "bin_color": "GREY",
            "environmental_impact": {
                "co2_saved_kg": 0. 0,
                "decomposition_time": "Unknown",
                "recycling_potential": "Unknown"
            },
            "additional_tips": [
                "Try taking a clearer photo",
                "Ensure good lighting",
                "Focus on one item at a time"
            ],
            "warnings": [
                "Could not identify waste type with high confidence"
            ],
            "alternatives": "Please try scanning again",
            "raw_ai_response": raw_response[:500]  # Include partial response for debugging
        }
    
    async def identify_waste(
        self, 
        image_data: bytes,
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Main method to identify waste from image
        
        Args:
            image_data: Image file as bytes
            user_context: Optional user information for personalized responses
            
        Returns:
            Dictionary containing waste identification results
            
        Example:
            >>> service = GeminiService()
            >>> with open("bottle.jpg", "rb") as f:
            ...     result = await service.identify_waste(f. read())
            >>> print(result["item_name"])
            "Plastic Water Bottle"
        """
        start_time = time.time()
        
        try:
            logger.info("🔍 Starting waste identification...")
            
            # Prepare image
            image = self._prepare_image(image_data)
            logger.info(f"✅ Image prepared: {image.size}")
            
            # Create prompt
            prompt = self._create_waste_identification_prompt()
            
            # Generate response from Gemini
            logger.info("🤖 Sending request to Gemini AI...")
            response = self.model.generate_content(
                [prompt, image],
                generation_config=genai.types.GenerationConfig(
                    temperature=settings.GEMINI_TEMPERATURE,
                    max_output_tokens=settings.GEMINI_MAX_TOKENS,
                )
            )
            
            # Parse response
            result = self._parse_gemini_response(response.text)
            
            # Add metadata
            result["processing_time_seconds"] = round(time.time() - start_time, 2)
            result["model_used"] = settings.GEMINI_MODEL
            result["timestamp"] = time.time()
            
            # Calculate points earned
            result["points_earned"] = self._calculate_points(result)
            
            logger.info(f"✅ Identification complete: {result['item_name']} ({result['confidence']:.2%} confidence)")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Waste identification failed: {str(e)}")
            return {
                "error": True,
                "error_message": str(e),
                "item_name": "Error",
                "category": "Unknown",
                "confidence": 0.0,
                "processing_time_seconds": round(time.time() - start_time, 2)
            }
    
    def _calculate_points(self, waste_data: Dict[str, Any]) -> int:
        """
        Calculate points earned based on waste identification
        
        Args:
            waste_data: Parsed waste identification results
            
        Returns:
            Points earned (integer)
        """
        base_points = settings.POINTS_CORRECT_DISPOSAL
        
        # Bonus for high confidence
        if waste_data. get("confidence", 0) >= 0.9:
            base_points += 10
        
        # Bonus for recyclable items
        if waste_data.get("recyclable", False):
            base_points += 20
        
        # Bonus for difficult categories (hazardous, e-waste)
        if waste_data.get("category") in ["Hazardous Waste", "E-Waste"]:
            base_points += 30
        
        return base_points
    
    async def get_educational_content(self, category: str) -> Dict[str, Any]:
        """
        Get educational content about a waste category
        
        Args:
            category: Waste category name
            
        Returns:
            Educational information dictionary
        """
        if category not in WASTE_DISPOSAL_GUIDES:
            return {"error": "Category not found"}
        
        guide = WASTE_DISPOSAL_GUIDES[category]
        
        # Generate additional AI insights
        prompt = f"""Provide 3 interesting facts about {category} waste and recycling. 
Format as JSON:
{{
    "facts": ["fact 1", "fact 2", "fact 3"],
    "global_impact": "one sentence about global impact",
    "did_you_know": "interesting statistic or fact"
}}"""
        
        try:
            response = self.model.generate_content(prompt)
            ai_content = json.loads(response.text. replace("```json", ""). replace("```", ""). strip())
            
            return {
                **guide,
                **ai_content,
                "category": category
            }
        except:
            return {
                **guide,
                "category": category
            }
    
    def validate_api_key(self) -> bool:
        """
        Validate that Gemini API key is working
        
        Returns:
            True if API key is valid, False otherwise
        """
        try:
            # Simple test generation
            response = self.model.generate_content("Say 'OK' if you can hear me")
            return bool(response.text)
        except Exception as e:
            logger.error(f"❌ API key validation failed: {str(e)}")
            return False


# ==================== SINGLETON INSTANCE ====================
_gemini_service_instance: Optional[GeminiService] = None


def get_gemini_service() -> GeminiService:
    """
    Get singleton instance of GeminiService
    
    Returns:
        GeminiService instance
        
    Example:
        >>> service = get_gemini_service()
        >>> result = await service.identify_waste(image_bytes)
    """
    global _gemini_service_instance
    
    if _gemini_service_instance is None:
        _gemini_service_instance = GeminiService()
    
    return _gemini_service_instance


# ==================== HELPER FUNCTIONS ====================

async def quick_identify(image_path: str) -> Dict[str, Any]:
    """
    Quick helper function to identify waste from image path
    
    Args:
        image_path: Path to image file
        
    Returns:
        Identification results
        
    Example:
        >>> result = await quick_identify("bottle. jpg")
        >>> print(result["category"])
    """
    with open(image_path, "rb") as f:
        image_data = f.read()
    
    service = get_gemini_service()
    return await service.identify_waste(image_data)


def format_disposal_instructions(waste_data: Dict[str, Any]) -> str:
    """
    Format disposal instructions as readable text
    
    Args:
        waste_data: Waste identification results
        
    Returns:
        Formatted instructions string
    """
    output = []
    output.append(f"📦 Item: {waste_data. get('item_name', 'Unknown')}")
    output.append(f"📁 Category: {waste_data. get('category', 'Unknown')}")
    output.append(f"🎯 Confidence: {waste_data.get('confidence', 0):.1%}")
    output.append(f"\n♻️ How to Dispose:")
    
    for i, step in enumerate(waste_data.get('disposal_steps', []), 1):
        output. append(f"  {i}. {step}")
    
    output.append(f"\n🗑️ Bin Color: {waste_data.get('bin_color', 'N/A')}")
    
    impact = waste_data.get('environmental_impact', {})
    if impact:
        output.append(f"\n🌍 Environmental Impact:")
        output.append(f"  • CO₂ Saved: {impact.get('co2_saved_kg', 0)} kg")
        output.append(f"  • Decomposition Time: {impact.get('decomposition_time', 'Unknown')}")
    
    if waste_data.get('warnings'):
        output.append(f"\n⚠️ Warnings:")
        for warning in waste_data['warnings']:
            output.append(f"  • {warning}")
    
    return "\n".join(output)
