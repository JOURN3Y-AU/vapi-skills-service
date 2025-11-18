"""
Authentication Utilities

Provides password hashing, verification, and session management
for the admin authentication system.
"""

import bcrypt
from typing import Optional
import re


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt

    Args:
        password: Plain text password

    Returns:
        Hashed password as string
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a password against a hash

    Args:
        password: Plain text password to verify
        password_hash: Stored bcrypt hash

    Returns:
        True if password matches, False otherwise
    """
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except Exception:
        return False


def validate_password_strength(password: str) -> dict:
    """
    Validate password strength according to requirements

    Requirements:
    - At least 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    - At least one special character

    Args:
        password: Password to validate

    Returns:
        Dict with 'valid' (bool), 'requirements' (dict), and 'strength' (str)
    """
    requirements = {
        'min_length': len(password) >= 8,
        'has_uppercase': bool(re.search(r'[A-Z]', password)),
        'has_lowercase': bool(re.search(r'[a-z]', password)),
        'has_number': bool(re.search(r'\d', password)),
        'has_special': bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
    }

    valid = all(requirements.values())

    # Calculate strength
    met_count = sum(requirements.values())
    if met_count <= 2:
        strength = 'weak'
    elif met_count <= 4:
        strength = 'medium'
    else:
        strength = 'strong'

    return {
        'valid': valid,
        'requirements': requirements,
        'strength': strength
    }


def get_password_requirements_text() -> dict:
    """
    Get user-friendly text for password requirements

    Returns:
        Dict mapping requirement keys to display text
    """
    return {
        'min_length': 'At least 8 characters',
        'has_uppercase': 'One uppercase letter (A-Z)',
        'has_lowercase': 'One lowercase letter (a-z)',
        'has_number': 'One number (0-9)',
        'has_special': 'One special character (!@#$%^&*...)'
    }
