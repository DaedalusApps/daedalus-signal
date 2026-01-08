"""
DaedalusSignal Configuration
"""
import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# Database
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR / 'daedalus.db'}")

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
BCRYPT_ROUNDS = 12

# Worker Authentication (for DreamHost worker communication)
WORKER_SECRET = os.getenv("WORKER_SECRET", "")

# DreamHost Worker Configuration
DREAMHOST_WORKER_URL = os.getenv("DREAMHOST_WORKER_URL", "")

# PythonAnywhere API URL (for workers to call back, and for unsubscribe links)
PA_API_URL = os.getenv("PA_API_URL", "https://signal.daedalusapps.com")

# Admin credentials (configure via environment variables)
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@daedalusapps.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "changeme123")

# Scraping settings
SCRAPE_DELAY_MIN = 2  # Minimum seconds between requests
SCRAPE_DELAY_MAX = 5  # Maximum seconds between requests
USER_AGENT_ROTATE = True

# Rate limiting
RATE_LIMIT_DEFAULT = "100 per hour"
RATE_LIMIT_LOGIN = "5 per minute"

# Email (console mode for local testing)
EMAIL_MODE = os.getenv("EMAIL_MODE", "console")  # "console" or "smtp"
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", "noreply@daedalusapps.com")

# Cloudflare Turnstile CAPTCHA
TURNSTILE_SECRET_KEY = os.getenv("TURNSTILE_SECRET_KEY", "")

# Verification codes
VERIFICATION_CODE_EXPIRY_MINUTES = 15

# User limits
MAX_SOURCES_PER_USER = 10
MAX_TAGS_PER_USER = 20

# CORS - Add your PythonAnywhere username and production domain
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    os.getenv("CORS_ORIGIN_1", "https://signal.daedalusapps.com"),
    os.getenv("CORS_ORIGIN_2", ""),
]
# Filter out empty strings
CORS_ORIGINS = [o for o in CORS_ORIGINS if o]
