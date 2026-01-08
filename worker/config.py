"""
DreamHost Worker Configuration
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from the same directory as this config
load_dotenv(Path(__file__).parent / '.env')

# PythonAnywhere API configuration
PA_API_URL = os.getenv("PA_API_URL", "https://your-username.pythonanywhere.com")
WORKER_SECRET = os.getenv("WORKER_SECRET", "")

# Local SMTP configuration (DreamHost's mail server)
SMTP_HOST = os.getenv("SMTP_HOST", "mail.yourdomain.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", "noreply@yourdomain.com")

# Scraping configuration
SCRAPE_DELAY_MIN = 2
SCRAPE_DELAY_MAX = 5
USER_AGENT_ROTATE = True
