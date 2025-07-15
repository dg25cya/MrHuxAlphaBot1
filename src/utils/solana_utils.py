"""Solana utility functions."""
import re
import base58
from typing import List, Dict, Any, Optional, Union
from loguru import logger

def is_valid_solana_address(address: str) -> bool:
    """
    Validate if a string is a valid Solana address.
    
    Args:
        address: The string to validate
        
    Returns:
        True if valid Solana address format, False otherwise
    """
    # Solana addresses are base58 encoded and 32-44 bytes
    if not address or not isinstance(address, str):
        return False
        
    # Check if address matches the expected pattern
    if not re.match(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$', address):
        return False
    
    # Validate as base58
    try:
        decoded = base58.b58decode(address)
        return len(decoded) in (32, 33, 34)  # Valid Solana key lengths
    except Exception as e:
        return False

def normalize_solana_address(address: str) -> str:
    """
    Normalize a Solana address to a standard format.
    
    Args:
        address: Solana address to normalize
        
    Returns:
        Normalized address
    """
    if not address:
        return ""
        
    # Remove spaces and any special characters
    normalized = re.sub(r'[^1-9A-HJ-NP-Za-km-z]', '', address)
    
    # If it looks like a valid address, return it
    if is_valid_solana_address(normalized):
        return normalized
    
    return address  # Return original if normalization fails

def extract_solana_addresses(text: str) -> List[str]:
    """
    Extract potential Solana addresses from text.
    
    Args:
        text: Text to extract addresses from
        
    Returns:
        List of potential Solana addresses
    """
    if not text:
        return []
        
    # Pattern to find potential Solana addresses
    pattern = r'[1-9A-HJ-NP-Za-km-z]{32,44}'
    
    # Find all matches
    addresses = re.findall(pattern, text)
    
    # Validate and filter
    return [addr for addr in addresses if is_valid_solana_address(addr)]

def generate_token_key(address: str) -> str:
    """
    Generate a consistent cache key for a token address.
    
    Args:
        address: Token address
        
    Returns:
        Cache key
    """
    normalized = normalize_solana_address(address)
    return f"token:{normalized}"
