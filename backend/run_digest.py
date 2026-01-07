"""
Run daily digest email task.
For PythonAnywhere scheduled tasks - runs once and exits.
"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.email import run_daily_digest

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        run_daily_digest()
