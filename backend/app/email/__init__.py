"""
Email package
"""
from app.email.digest import generate_digest, send_digest, run_daily_digest
from app.email.verification import (
    generate_verification_code,
    get_code_expiry,
    send_verification_email
)

__all__ = [
    'generate_digest',
    'send_digest',
    'run_daily_digest',
    'generate_verification_code',
    'get_code_expiry',
    'send_verification_email'
]
