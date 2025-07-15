"""Text formatting utilities."""
import re
import emoji
from typing import List, Dict, Any

def clean_text(text: str) -> str:
    """
    Clean text by removing special characters and normalizing whitespace.
    
    Args:
        text (str): Text to clean
        
    Returns:
        str: Cleaned text
    """
    # Remove special characters and normalize whitespace
    text = re.sub(r'[^\w\s]', ' ', text)
    return " ".join(text.split())

def extract_entities(text: str) -> Dict[str, List[str]]:
    """
    Extract entities like URLs, hashtags, and mentions from text.
    
    Args:
        text (str): Text to analyze
        
    Returns:
        Dict[str, List[str]]: Dictionary containing lists of entities
    """
    entities = {
        'urls': re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text),
        'hashtags': re.findall(r'#(\w+)', text),
        'mentions': re.findall(r'@(\w+)', text)
    }
    return entities

class TextFormatter:
    """Class for text formatting operations."""
    
    @staticmethod
    def format_message(message: str, emojis: bool = True) -> str:
        """
        Format a message with optional emoji support.
        
        Args:
            message (str): The message to format
            emojis (bool): Whether to include emojis in formatting
            
        Returns:
            str: The formatted message
        """
        if emojis:
            return emoji.emojize(message, use_aliases=True)
        return message
        
    @staticmethod
    def truncate(text: str, max_length: int = 100, suffix: str = "...") -> str:
        """
        Truncate text to specified length with suffix.
        
        Args:
            text (str): Text to truncate
            max_length (int): Maximum length before truncation
            suffix (str): Suffix to add to truncated text
            
        Returns:
            str: Truncated text
        """
        if len(text) <= max_length:
            return text
        return text[:max_length - len(suffix)] + suffix
