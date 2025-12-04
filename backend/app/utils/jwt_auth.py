import jwt
import os
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
from app.models.models import User

# Get JWT secret from environment, fallback to default for development
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

def generate_token(user_id, role):
    """
    Generate access and refresh tokens for a user.
    
    Args:
        user_id: User ID
        role: User role (e.g., 'user', 'admin')
    
    Returns:
        dict: Contains access_token and refresh_token
    """
    # Access token payload
    access_payload = {
        'user_id': user_id,
        'role': role,
        'exp': datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        'iat': datetime.utcnow(),
        'type': 'access'
    }
    
    # Refresh token payload
    refresh_payload = {
        'user_id': user_id,
        'role': role,
        'exp': datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        'iat': datetime.utcnow(),
        'type': 'refresh'
    }
    
    access_token = jwt.encode(access_payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    refresh_token = jwt.encode(refresh_payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    
    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_type': 'bearer'
    }

def verify_token(token):
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token string
    
    Returns:
        dict: Decoded token payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def get_user_from_token(token):
    """
    Extract user information from a JWT token.
    
    Args:
        token: JWT token string
    
    Returns:
        dict: User info (user_id, role) if valid, None otherwise
    """
    payload = verify_token(token)
    if payload:
        return {
            'user_id': payload.get('user_id'),
            'role': payload.get('role'),
            'token_type': payload.get('type')
        }
    return None

def extract_token_from_header():
    """
    Extract JWT token from Authorization header.
    
    Returns:
        str: Token string if found, None otherwise
    """
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None
    
    try:
        # Format: "Bearer <token>"
        token = auth_header.split(' ')[1]
        return token
    except IndexError:
        return None

