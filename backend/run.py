"""
Run the DaedalusSignal backend server
"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from scheduler import create_scheduler

app = create_app()


def run_server():
    """Run the development server with scheduler."""
    # Start the background scheduler
    scheduler = create_scheduler()
    scheduler.start()
    print("✓ Background scheduler started")
    print("  - Content ingestion: every 6 hours")
    print("  - Daily digest: 8:00 AM")
    
    print("\n🚀 Starting DaedalusSignal API server...")
    print("   API: http://localhost:5000")
    print("   Health: http://localhost:5000/api/health\n")
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
    except KeyboardInterrupt:
        print("\nShutting down...")
        scheduler.shutdown()


if __name__ == '__main__':
    run_server()
