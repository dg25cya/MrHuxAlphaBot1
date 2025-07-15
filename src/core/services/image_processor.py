"""Image processing service for OCR and text extraction."""
import io
import cv2
from PIL import Image
# import easyocr  # DISABLED for free hosting
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
    """Service for processing images and extracting text. (DISABLED for free hosting)"""

    def __init__(self) -> None:
        """Initialize OCR reader and image processing tools. (DISABLED)"""
        # self.reader = easyocr.Reader(['en'])  # DISABLED
        self.http_client = httpx.AsyncClient(timeout=30.0)

    async def process_image(self, image_data: bytes) -> List[ImageRegion]:
        """
        Disabled: Always returns empty list.
        """
        logger.warning("OCR/image processing is disabled for free hosting.")
        return []

    async def download_image(self, url: str) -> Optional[bytes]:
        try:
            async with self.http_client.stream('GET', url) as response:
                if response.status_code == 200:
                    return await response.aread()
            return None
        except Exception as e:
            logger.error(f"Error downloading image from {url}: {str(e)}")
            return None

    def _bytes_to_image(self, image_data: bytes) -> Image.Image:
        return Image.open(io.BytesIO(image_data))

    def _preprocess_image(self, img: Image.Image) -> Image.Image:
        return img  # No-op

    async def close(self):
        if self.http_client:
            await self.http_client.aclose()

    def some_method(self) -> None:
        pass

# Restore singleton for import compatibility
image_processor = ImageProcessor()
