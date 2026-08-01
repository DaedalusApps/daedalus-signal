# DaedalusSignal

A self-hosted content aggregator that scrapes YouTube and X (via Nitter), lets each user curate their own sources/tags, and delivers a personalized feed plus a daily email digest. Includes an admin dashboard for managing defaults and reviewing user-submitted sources.

## Features
- Aggregates content from YouTube and X (Twitter, via Nitter scraping)
- Per-user sources (20) and tags (50), with a personalized feed
- Daily email digest (opt-out available)
- Admin dashboard for managing default sources/tags and approving user submissions
- Optional per-item relevance scoring on ingestion (items scoring below 10 are dropped); the bundled scrapers don't currently produce scores, so no filtering happens in practice — see [Architecture](#architecture)

## Architecture

| Component | Technology | Description |
|-----------|------------|--------------|
| Frontend | Next.js (Static Export) | Hosted on DreamHost |
| Backend | PHP API | Hosted on DreamHost |
| Workers | Python (cron jobs) | Content scraping & email delivery |
| Database | MySQL | DreamHost MySQL |

The worker's ingestion route (`api/routes/worker.php`) accepts an optional `relevance_score` per item and drops items scoring below `10`; a missing score defaults to `50` (passes the filter). The bundled scrapers don't currently compute a score, so nothing is filtered in practice today.

Scrapers rotate user-agent strings when polling YouTube and Nitter to avoid aggressive rate limiting. This is ToS-adjacent scraping behavior, stated here openly.

## Environment Variables

- **API**: all API environment variables (DB credentials, `JWT_SECRET`, `SECRET_KEY`, CORS, SMTP, admin seed credentials, etc.) are documented in [`api/htaccess.example`](api/htaccess.example) — that file is the single source of truth and the only copy tracked in this repo. Copy it to `api/.htaccess` (untracked, git-ignored) and fill in real values there — never commit real values.
- **Workers**: see [`worker/.env.example`](worker/.env.example) for the Python worker's configuration (API URL, shared `SECRET_KEY`, SMTP settings).
- **Frontend** (`frontend/.env.local` for dev, `.env.production` for builds):

  | Variable | Description |
  |----------|--------------|
  | `NEXT_PUBLIC_API_URL` | Site root that serves the API (no trailing slash, no `/api` suffix — the code appends it). Leave unset for same-origin requests (`''`); in `next dev` this means requests go to `localhost:3000` and will fail unless you set it, which triggers a console warning in non-production builds. |
  | `NEXT_PUBLIC_TURNSTILE_SITE_KEY` | Cloudflare Turnstile site key (CAPTCHA) |
  | `NEXT_PUBLIC_DREAMHOST_WORKER_URL` | Optional URL of `worker/web_shim.php`, used for the admin dashboard's test-email feature. Leave unset to disable it. |

## Quick Start (Local Development)

This sets up a local database and API — it never touches the production DreamHost environment.

Commands below assume a bash shell (Git Bash or WSL on Windows).

### Prerequisites
- PHP 8+
- MySQL or MariaDB
- Node.js >= 18.17
- Python >= 3.10 (only needed to run the scrapers/mailer worker locally)

### 1. Database

Create a local database and apply the migrations in order:

```bash
mysql -u root -p -e "CREATE DATABASE daedalussignal"
mysql -u root -p daedalussignal < api/migrations/000_initial_schema.sql
mysql -u root -p daedalussignal < api/migrations/001_password_reset_tokens.sql
```

`000_initial_schema.sql` was reconstructed from the API code (the original Flask backend and its migrations were deleted before the DreamHost PHP API took over) — see the comment at the top of that file. If you have access to the original production database, diff against it first:

```bash
mysqldump --no-data daedalussignal
```

### 2. API

Generate secrets for `JWT_SECRET` and `SECRET_KEY`:

```bash
openssl rand -hex 32
```

(`openssl` ships with Git Bash and WSL on Windows; use either if you're on `cmd`/PowerShell without it installed.)

The API reads its configuration from environment variables — normally supplied via `.htaccess` `SetEnv` in production (see [`api/htaccess.example`](api/htaccess.example)), but the PHP built-in server does not process `.htaccess`. For local dev, export the variables in your shell before starting the server:

```bash
cd api
export DB_HOST=localhost DB_NAME=daedalussignal DB_USER=root DB_PASSWORD=yourpassword
export JWT_SECRET=$(openssl rand -hex 32)
export SECRET_KEY=$(openssl rand -hex 32)
export TURNSTILE_SECRET_KEY=1x0000000000000000000000000000000AA
php -S localhost:8000 api.php
```

`TURNSTILE_SECRET_KEY` is unset otherwise, and `POST /auth/register` fails closed without it (see `api/lib/auth.php`); the value above is Cloudflare's public dummy secret key that always passes — use a real key in production.

Note the `api.php` argument — it's used as a router script so every request (e.g. `/health`, `/auth/login`) gets dispatched through the same routing logic used in production. Without it, the built-in server 404s on anything that isn't a literal file. Verify it's working:

```bash
curl http://localhost:8000/health
# {"status":"ok","timestamp":"..."}
```

`php -S` above blocks the terminal, so seed from a **second terminal**. The seeder is a separate CLI process and does not inherit the first terminal's exports, so re-export `DB_HOST`/`DB_NAME`/`DB_USER`/`DB_PASSWORD` (from the block above) there too, along with the admin credentials, before running it (still in the `api/` directory):

```bash
export DB_HOST=localhost DB_NAME=daedalussignal DB_USER=root DB_PASSWORD=yourpassword
export ADMIN_EMAIL=you@example.com
export ADMIN_PASSWORD=use-a-strong-password-here
php seed.php
```

`seed.php` hard-fails if `ADMIN_EMAIL`/`ADMIN_PASSWORD` aren't set — there is no default credential.

### 3. Frontend

```bash
cd frontend
cp .env.example .env.local
# set NEXT_PUBLIC_API_URL=http://localhost:8000 in .env.local
# set NEXT_PUBLIC_TURNSTILE_SITE_KEY=1x00000000000000000000AA in .env.local
npm install
npm run dev
```

Visit `http://localhost:3000`.

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for production deployment instructions (DreamHost).

## License
[MIT](LICENSE)
