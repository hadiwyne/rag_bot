import pytest
from app.core.security import SecurityService

def test_password_hashing():
    """Test password hashing and verification"""
    password = "testpassword123"
    hashed = SecurityService.get_password_hash(password)
    
    assert SecurityService.verify_password(password, hashed) == True
    assert SecurityService.verify_password("wrongpassword", hashed) == False

def test_jwt_token():
    """Test JWT token creation and verification"""
    data = {"sub": "testuser"}
    token = SecurityService.create_access_token(data)
    
    decoded = SecurityService.verify_token(token)
    assert decoded["sub"] == "testuser"

def test_input_sanitization():
    """Test input sanitization"""
    malicious_input = "<script>alert('xss')</script>" + "A" * 2000
    sanitized = SecurityService.sanitize_input(malicious_input)
    
    assert len(sanitized) <= 1000
    assert sanitized == malicious_input[:1000].strip()