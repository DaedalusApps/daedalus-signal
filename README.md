# DaedalusSignal

A self-hosted modular intelligence system that aggregates, filters, and surfaces high-signal content about agentic development, context engineering, and frontier AI tooling.

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+

### Backend Setup
```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py
```

### Frontend Setup
```powershell
cd frontend
npm install
npm run dev
```

### Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5000

## Features
- Aggregates content from YouTube, X (Twitter), LinkedIn, GitHub
- Keyword and semantic filtering
- Daily email digest (opt-out available)
- Customizable sources (10) and tags (20) per user
- Admin panel for managing defaults

## Architecture
- **Frontend**: Next.js static export
- **Backend**: Flask + SQLAlchemy
- **Database**: SQLite (stored in /data)
- **Scraping**: Respectful rate-limited scrapers

## License
MIT
