"""
DreamHost Worker Configuration
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from the same directory as this config
load_dotenv(Path(__file__).parent / '.env')

# API configuration (DreamHost PHP API)
API_URL = os.getenv("API_URL", "https://signal.daedalusapps.com/api")
SECRET_KEY = os.getenv("SECRET_KEY", "")

# Local SMTP configuration (DreamHost's mail server)
SMTP_HOST = os.getenv("SMTP_HOST", "mail.signal.daedalusapps.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", "noreply@signal.daedalusapps.com")

# Scraping configuration
SCRAPE_DELAY_MIN = 2
SCRAPE_DELAY_MAX = 5
USER_AGENT_ROTATE = True
