# Deploying Daedalus Signal

This guide covers deploying to **DreamHost** (all components).

## Architecture

| Component | Host | URL |
|-----------|------|-----|
| Frontend (Static) | DreamHost | `signal.daedalusapps.com` |
| Backend API | DreamHost | `signal.daedalusapps.com/api` |
| Workers | DreamHost | Cron jobs |
| Database | DreamHost | MySQL |

---

## Part 1: PHP API

### 1. Upload API Files

Upload the `api/` folder to your DreamHost domain directory:

```bash
scp -r api/* user@server.dreamhost.com:~/signal.daedalusapps.com/api/
```

### 2. Install Dependencies

SSH to DreamHost and install Composer dependencies:

```bash
cd ~/signal.daedalusapps.com/api
composer install
```

### 3. Configure Environment

Merge the `SetEnv` block from `api/htaccess.example` into the deployed `api/.htaccess` (or copy `htaccess.example` to `.htaccess` on the server) and fill in real values:

```apache
SetEnv DB_HOST your_mysql_hostname
SetEnv DB_NAME your_database_name
SetEnv DB_USER your_database_user
SetEnv DB_PASSWORD your_database_password
SetEnv JWT_SECRET your_256_bit_random_secret
SetEnv SECRET_KEY your_hmac_secret_for_workers
SetEnv TURNSTILE_SECRET_KEY your_cloudflare_turnstile_key
# Set a strong, unique admin password - there is no default credential
SetEnv ADMIN_EMAIL your_admin_email@example.com
SetEnv ADMIN_PASSWORD your_strong_admin_password
# Comma-separated list of allowed CORS origins; unset = built-in defaults
# (includes localhost dev origins). Set explicitly in production.
SetEnv CORS_ALLOWED_ORIGINS https://your-frontend-domain.com
```

See `api/htaccess.example` for the complete file (rewrite rules + full `SetEnv` block, including `SEED_KEY`, `FRONTEND_URL`, and `SMTP_*` variables).

### 4. Create MySQL Database

1. Log in to DreamHost panel
2. Go to **MySQL Databases**
3. Create a new database and user
4. Note the hostname (e.g., `mysql.example.com`)

### 5. Seed Database

Run the seeder to create default sources, tags, and admin user:

```bash
php ~/signal.daedalusapps.com/api/seed.php
```

Or via web (if SEED_KEY is set):
```
https://signal.daedalusapps.com/api/seed.php?key=YOUR_SEED_KEY
```

### 6. Verify API

```bash
curl https://signal.daedalusapps.com/api/health
# Should return: {"status":"ok","timestamp":"..."}
```

---

## Part 2: Frontend

### 1. Build for Production

On your local machine:

1. Create `frontend/.env.production`:
```ini
NEXT_PUBLIC_API_URL=https://signal.daedalusapps.com
```

2. Build:
```bash
cd frontend
npm run build
```

This creates an `out/` folder with static files.

### 2. Upload to DreamHost

Upload contents of `out/` folder to the domain root:

```bash
scp -r frontend/out/* user@server.dreamhost.com:~/signal.daedalusapps.com/
```

Ensure `index.html` is in the root (not inside an `out/` subfolder).

### 3. Verify .htaccess

The `frontend/out/.htaccess` should be uploaded for SPA routing:

```apache
<IfModule mod_rewrite.c>
  RewriteEngine On
  RewriteBase /
  RewriteRule ^index\.html$ - [L]
  RewriteCond %{REQUEST_FILENAME} !-f
  RewriteCond %{REQUEST_FILENAME} !-d
  RewriteCond %{REQUEST_FILENAME} !-l
  RewriteRule . /index.html [L]
</IfModule>
```

---

## Part 3: Workers (Cron Jobs)

### 1. Upload Worker Files

```bash
ssh user@server.dreamhost.com
mkdir -p ~/worker
```

```bash
scp -r worker/* user@server.dreamhost.com:~/worker/
```

### 2. Set Up Python Environment

```bash
cd ~/worker
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure Worker Environment

Create `~/worker/.env`:

```bash
API_URL=https://signal.daedalusapps.com/api
SECRET_KEY=same_as_api_secret_key

SMTP_HOST=mail.signal.daedalusapps.com
SMTP_PORT=587
SMTP_USER=noreply@signal.daedalusapps.com
SMTP_PASSWORD=your_smtp_password
SMTP_FROM=noreply@signal.daedalusapps.com
```

### 4. Create Wrapper Script

Create `~/worker/run.sh`:

```bash
#!/bin/bash
cd ~/worker
source venv/bin/activate
source .env
export API_URL SECRET_KEY SMTP_HOST SMTP_PORT SMTP_USER SMTP_PASSWORD SMTP_FROM
python "$@"
```

```bash
chmod +x ~/worker/run.sh
```

### 5. Set Up Cron Jobs

```bash
mkdir -p ~/logs
crontab -e
```

Add:

```cron
# Scrape content every 6 hours
0 */6 * * * cd ~/worker && ./run.sh run_scrapers.py >> ~/logs/scraper.log 2>&1

# Send daily digests at 8 AM
0 8 * * * cd ~/worker && ./run.sh run_mailer.py >> ~/logs/mailer.log 2>&1
```

### 6. Test Workers Manually

```bash
cd ~/worker
./run.sh run_scrapers.py
./run.sh run_mailer.py
```

---

## Part 4: Verify Deployment

1. **API Health**: `https://signal.daedalusapps.com/api/health`
   - Should return: `{"status":"ok","timestamp":"..."}`

2. **Frontend**: `https://signal.daedalusapps.com`
   - Should load the app

3. **Login**: Test with admin credentials

4. **Cron Jobs**: Check logs after scheduled times
   - `tail -f ~/logs/scraper.log`
   - `tail -f ~/logs/mailer.log`

---

## Troubleshooting

### CORS Errors
- Check `api/lib/cors.php` has correct allowed origins
- Verify `.htaccess` is being processed

### Database Connection Errors
- Verify DB credentials in `.htaccess`
- Check MySQL hostname format

### Worker Authentication Errors
- Ensure `SECRET_KEY` matches between API and workers
- Check server time sync (signatures have 5-minute window)

### Static Files Not Loading
- Ensure `out/` folder contents (not the folder itself) are in the domain root
- Verify `.htaccess` is present and correct
