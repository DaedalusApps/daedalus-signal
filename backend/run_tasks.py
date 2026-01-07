"""
Combined scheduled task runner.
Runs both content ingestion and daily digest check.
For PythonAnywhere free tier - runs once and exits.
"""
import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from scheduler import scrape_all_sources
from app.email import run_daily_digest

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        print(f"[{datetime.now()}] Running scheduled tasks...")
        
        # Always run content ingestion
        print("Running content ingestion...")
        scrape_all_sources()
        
        # Check if it's around 8 AM (7-9 AM window) to send digest
        current_hour = datetime.now().hour
        if 7 <= current_hour <= 9:
            print("Running daily digest...")
            run_daily_digest()
        else:
            print(f"Skipping digest (current hour: {current_hour}, runs 7-9 AM)")
        
        print(f"[{datetime.now()}] Scheduled tasks complete!")
