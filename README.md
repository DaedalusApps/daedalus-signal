# DaedalusSignal

A self-hosted modular intelligence system that aggregates, filters, and surfaces high-signal content about agentic development, context engineering, and frontier AI tooling.

## Quick Start (Local Development)

### Prerequisites
- Python 3.10+
- Node.js 18+

### Option 1: Use Startup Script (Windows)
```powershell
.\_docs\startup.ps1
```

### Option 2: Manual Setup

**Backend:**
```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env  # Edit with your settings
python seed.py        # Initialize database
python run.py         # Start API server
```

**Frontend:**
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

| Component | Technology | Description |
|-----------|------------|-------------|
| Frontend | Next.js (Static Export) | Hosted on DreamHost |
| Backend | Flask + SQLAlchemy | Hosted on PythonAnywhere |
| Database | SQLite (dev) / MySQL (prod) | PythonAnywhere MySQL |

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for production deployment instructions.

## Environment Variables

### Backend (`backend/.env`)
| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Flask session secret |
| `DATABASE_URL` | Database connection string |
| `ADMIN_EMAIL` | Admin login email |
| `ADMIN_PASSWORD` | Admin login password |
| `EMAIL_MODE` | `console` or `smtp` |
| `CORS_ORIGIN_1` | Frontend domain for CORS |

### Frontend (`frontend/.env.local`)
| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_API_URL` | Backend API URL |

## License
MIT
