# DaedalusSignal

A self-hosted modular intelligence system that aggregates, filters, and surfaces high-signal content about agentic development, context engineering, and frontier AI tooling.

## Quick Start (Local Development)

### Prerequisites
- Node.js 18+
- PHP 8+ (optional, for local API testing)

### Option 1: Use Startup Script (Windows)
```powershell
.\_docs\startup.ps1
```

### Option 2: Manual Setup

**Frontend:**
```powershell
cd frontend
npm install
npm run dev
```

The frontend connects to the production API at `https://signal.daedalusapps.com/api` by default.

### Access the Application
- **Frontend**: http://localhost:3000
- **API**: https://signal.daedalusapps.com/api

## Features
- Aggregates content from YouTube, X (Twitter)
- Keyword and semantic filtering
- Daily email digest (opt-out available)
- Customizable sources (10) and tags (20) per user
- Admin panel for managing defaults

## Architecture

| Component | Technology | Description |
|-----------|------------|-------------|
| Frontend | Next.js (Static Export) | Hosted on DreamHost |
| Backend | PHP API | Hosted on DreamHost |
| Workers | Python (cron jobs) | Content scraping & email delivery |
| Database | MySQL | DreamHost MySQL |

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for production deployment instructions.

## Environment Variables

### API (`api/.htaccess` SetEnv)
| Variable | Description |
|----------|-------------|
| `DB_HOST` | MySQL host |
| `DB_NAME` | Database name |
| `DB_USER` | Database user |
| `DB_PASSWORD` | Database password |
| `JWT_SECRET` | JWT signing key |
| `SECRET_KEY` | HMAC key for workers |
| `TURNSTILE_SECRET_KEY` | Cloudflare CAPTCHA |

### Frontend (`frontend/.env.local`)
| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_API_URL` | Backend API URL |

### Workers (`worker/.env`)
| Variable | Description |
|----------|-------------|
| `API_URL` | PHP API URL |
| `SECRET_KEY` | Must match API's SECRET_KEY |
| `SMTP_*` | Email server settings |

## Database Seeding

To seed the database with default sources and tags:
```bash
php api/seed.php
```

## License
[MIT](LICENSE)
