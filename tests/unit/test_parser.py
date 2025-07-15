"""Unit tests for the token parser."""
import pytest
from src.core.services.parser import TokenParser, TokenMatch

def test_extract_raw_address():
    """Test extracting raw Solana addresses."""
    text = "Check out this token: So11111111111111111111111111111111111111111"
    tokens = TokenParser.extract_tokens(text)
    
    assert len(tokens) == 1
    assert tokens[0].address == "So11111111111111111111111111111111111111111"
    assert tokens[0].source == "address"

def test_extract_pump_fun_link():
    """Test extracting Pump.fun links."""
    text = "New token on pump.fun/token/So11111111111111111111111111111111111111111"
    tokens = TokenParser.extract_tokens(text)
    
    assert len(tokens) == 1
    assert tokens[0].address == "So11111111111111111111111111111111111111111"
    assert tokens[0].source == "pump_fun"

def test_extract_bonk_fun_link():
    """Test extracting Bonk.fun links."""
    text = "Check bonk.fun/token/So11111111111111111111111111111111111111111"
    tokens = TokenParser.extract_tokens(text)
    
    assert len(tokens) == 1
    assert tokens[0].address == "So11111111111111111111111111111111111111111"
    assert tokens[0].source == "bonk_fun"

def test_extract_multiple_tokens():
    """Test extracting multiple tokens from single message."""
    text = """
    Token 1: So11111111111111111111111111111111111111111
    Also on pump.fun/token/So22222222222222222222222222222222222222222
    And bonk.fun/token/So33333333333333333333333333333333333333333
    """
    tokens = TokenParser.extract_tokens(text)
    
    assert len(tokens) == 3
    assert {t.source for t in tokens} == {"address", "pump_fun", "bonk_fun"}

def test_no_token_found():
    """Test handling text without tokens."""
    text = "Just a regular message without any tokens"
    tokens = TokenParser.extract_tokens(text)
    
    assert len(tokens) == 0

def test_invalid_address_format():
    """Test handling invalid address formats."""
    text = "Invalid: notavalidaddress123"
    tokens = TokenParser.extract_tokens(text)
    
    assert len(tokens) == 0

def test_is_valid_solana_address():
    """Test Solana address validation."""
    assert TokenParser.is_valid_solana_address("So11111111111111111111111111111111111111111")
    assert not TokenParser.is_valid_solana_address("invalid123")
    assert not TokenParser.is_valid_solana_address("")

def test_extract_first_token():
    """Test extracting first token from text."""
    text = """
    First: So11111111111111111111111111111111111111111
    Second: So22222222222222222222222222222222222222222
    """
    token = TokenParser.extract_first_token(text)
    
    assert token is not None
    assert token.address == "So11111111111111111111111111111111111111111"
