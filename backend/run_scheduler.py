"""
Run content ingestion task.
For PythonAnywhere scheduled tasks - runs once and exits.
"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from scheduler import scrape_all_sources

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        scrape_all_sources()
