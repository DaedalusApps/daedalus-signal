"""
Email package
"""
from app.email.digest import generate_digest, send_digest, run_daily_digest

__all__ = ['generate_digest', 'send_digest', 'run_daily_digest']
