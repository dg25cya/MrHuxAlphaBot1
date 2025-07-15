"""Image processing service for OCR and text extraction."""
import io
import cv2
from PIL import Image
import easyocr
from loguru import logger
from typing import List, Optional, Tuple
import httpx
from dataclasses import dataclass
from ...utils.metrics_registry import metrics

@dataclass
class ImageRegion:
    """Container for detected text regions."""
    text: str
    confidence: float
    bbox: List[List[int]]  # Bounding box coordinates

class ImageProcessor:
    """Service for processing images and extracting text."""

    def __init__(self) -> None:
        """Initialize OCR reader and image processing tools."""
        # Initialize EasyOCR with English language
        self.reader = easyocr.Reader(['en'])
        
        # Configure HTTP client for downloading images
        self.http_client = httpx.AsyncClient(timeout=30.0)

    async def process_image(self, image_data: bytes) -> List[ImageRegion]:
        """
        Process image data and extract text regions with OCR.
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            List of ImageRegion objects containing extracted text and metadata
        """
        try:
            start_time = metrics.token_parser_ocr_start.labels(source='image').start()
            
            # Convert bytes to image
            img = self._bytes_to_image(image_data)
            
            # Preprocess image for better OCR
            img = self._preprocess_image(img)
            
            # Run OCR
            results = self.reader.readtext(np.array(img))
            
            # Convert results to ImageRegion objects
            regions = []
            for (bbox, text, conf) in results:
                if conf > 0.5:  # Filter low confidence results
                    regions.append(ImageRegion(
                        text=text,
                        confidence=conf,
                        bbox=bbox
                    ))
            
            metrics.token_parser_ocr_end.labels(source='image').observe(metrics.token_parser_ocr_duration.labels(source='image').elapsed(start_time))
            metrics.token_parser_ocr_regions.labels(source='image').inc(len(regions))
            
            return regions
            
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            metrics.token_parser_ocr_error.labels(source='image').inc()
            return []

    async def download_image(self, url: str) -> Optional[bytes]:
        """
        Download image from URL.
        
        Args:
            url: Image URL to download
            
        Returns:
            Image bytes if successful, None otherwise
        """
        try:
            async with self.http_client.stream('GET', url) as response:
                if response.status_code == 200:
                    return await response.aread()
                    
            metrics.token_parser_ocr_error.labels(source='image').inc()
            return None
            
        except Exception as e:
            logger.error(f"Error downloading image from {url}: {str(e)}")
            metrics.token_parser_ocr_error.labels(source='image').inc()
            return None

    def _bytes_to_image(self, image_data: bytes) -> Image.Image:
        """Convert bytes to PIL Image."""
        return Image.open(io.BytesIO(image_data))

    def _preprocess_image(self, img: Image.Image) -> Image.Image:
        """
        Preprocess image for better OCR results.
        
        Applies:
        - Resize if too large
        - Contrast enhancement
        - Noise reduction
        - Text region detection
        """
        # Convert to OpenCV format
        img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        
        # Resize if too large (max 1920px width)
        max_width = 1920
        if img_cv.shape[1] > max_width:
            height = int(max_width * img_cv.shape[0] / img_cv.shape[1])
            img_cv = cv2.resize(img_cv, (max_width, height))
        
        # Apply adaptive histogram equalization for better contrast
        lab = cv2.cvtColor(img_cv, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        l = clahe.apply(l)
        lab = cv2.merge((l,a,b))
        img_cv = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        
        # Denoise
        img_cv = cv2.fastNlMeansDenoisingColored(img_cv)
        
        # Convert back to PIL
        return Image.fromarray(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB))

    async def close(self):
        """Clean up resources."""
        if self.http_client:
            await self.http_client.aclose()

    def some_method(self) -> None:
        # Example usage (replace with actual metric usage if available)
        # metrics.token_parser_processed.labels(source='image').inc()
        pass

# Create singleton instance
image_processor = ImageProcessor()
