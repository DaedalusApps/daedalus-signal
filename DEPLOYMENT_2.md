# DreamHost Worker Deployment Plan

This guide walks you through deploying the DreamHost Worker architecture to bypass PythonAnywhere free tier restrictions.

## Prerequisites

- PythonAnywhere account with your Flask app already deployed
- DreamHost hosting account with SSH access
- Domain configured on DreamHost (e.g., `worker.yourdomain.com`)

---

## Phase 1: Generate Secrets

Before deploying, generate a strong `WORKER_SECRET`:

```bash
# Generate a 64-character random secret
python -c "import secrets; print(secrets.token_hex(32))"
```

Save this value - you'll need it for both PythonAnywhere and DreamHost.

---

## Phase 2: Deploy Backend Changes to PythonAnywhere

### Step 2.1: Pull Latest Code

SSH into PythonAnywhere or use the web console:

```bash
cd ~/daedalus-signal
git pull origin main
```

### Step 2.2: Set Environment Variables

Go to **Web** tab > **WSGI configuration file** or add to your `.env`:

```bash
# Required for worker communication
WORKER_SECRET=<your-64-character-secret>

# Your PA app's public URL
PA_API_URL=https://your-username.pythonanywhere.com
```

Or set in the PythonAnywhere **Web** tab environment variables section.

### Step 2.3: Reload the Web App

Click **Reload** on the Web tab to apply changes.

### Step 2.4: Verify Worker API

Test that the worker endpoint is accessible (should return 401 without auth):

```bash
curl https://your-username.pythonanywhere.com/api/worker/sources
# Expected: {"error": "Missing worker authentication headers"}
```

---

## Phase 3: Deploy Worker to DreamHost

### Step 3.1: Create Worker Directory

SSH into DreamHost:

```bash
ssh username@server.dreamhost.com
mkdir -p ~/worker
cd ~/worker
```

### Step 3.2: Upload Worker Files

From your local machine:

```bash
cd daedalus-signal
scp -r worker/* username@server.dreamhost.com:~/worker/
```

Or clone the repo and copy:

```bash
git clone https://github.com/your-repo/daedalus-signal.git /tmp/daedalus
cp -r /tmp/daedalus/worker/* ~/worker/
```

### Step 3.3: Create Python Virtual Environment

```bash
cd ~/worker
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 3.4: Configure Worker Environment

Create `~/worker/.env`:

```bash
cat > ~/worker/.env << 'EOF'
# PythonAnywhere API Configuration
PA_API_URL=https://your-username.pythonanywhere.com
WORKER_SECRET=<same-64-character-secret-as-PA>

# DreamHost SMTP Configuration
SMTP_HOST=mail.yourdomain.com
SMTP_PORT=587
SMTP_USER=noreply@yourdomain.com
SMTP_PASSWORD=your-smtp-password
SMTP_FROM=noreply@yourdomain.com
EOF
```

### Step 3.5: Create Wrapper Script

Create `~/worker/run.sh`:

```bash
cat > ~/worker/run.sh << 'EOF'
#!/bin/bash
cd ~/worker
source venv/bin/activate
source .env
export PA_API_URL WORKER_SECRET SMTP_HOST SMTP_PORT SMTP_USER SMTP_PASSWORD SMTP_FROM
python "$@"
EOF
chmod +x ~/worker/run.sh
```

### Step 3.6: Test Scraper Manually

```bash
cd ~/worker
./run.sh run_scrapers.py
```

Expected output:
```
[2025-01-07 12:00:00] Starting DreamHost scraper worker...
  Fetched 5 sources from PythonAnywhere
  Scraping: Example YouTube Channel (youtube)
    Found 10 items
    Submitted: 8 added, 2 skipped
...
[2025-01-07 12:05:00] Scraper worker complete
```

### Step 3.7: Test Mailer Manually

```bash
./run.sh run_mailer.py
```

---

## Phase 4: Set Up Cron Jobs

Edit crontab:

```bash
crontab -e
```

Add these lines:

```cron
# Run scrapers every 6 hours
0 */6 * * * cd ~/worker && ./run.sh run_scrapers.py >> ~/logs/scraper.log 2>&1

# Send daily digests at 8 AM
0 8 * * * cd ~/worker && ./run.sh run_mailer.py >> ~/logs/mailer.log 2>&1
```

Create logs directory:

```bash
mkdir -p ~/logs
```

---

## Phase 5: Deploy PHP Web Shim (Optional - for Test Emails)

This is only needed if you want the "Send Test Email" button in the admin panel to work via DreamHost.

### Step 5.1: Upload PHP File

Copy `web_shim.php` to a web-accessible directory:

```bash
cp ~/worker/web_shim.php ~/yourdomain.com/worker/web_shim.php
```

### Step 5.2: Set PHP Environment Variables

Create `.htaccess` in the same directory:

```bash
cat > ~/yourdomain.com/worker/.htaccess << 'EOF'
SetEnv SECRET_KEY your-flask-secret-key
SetEnv SMTP_FROM noreply@yourdomain.com
EOF
```

**IMPORTANT**: The `SECRET_KEY` here must match your Flask app's `SECRET_KEY` (not `WORKER_SECRET`).

### Step 5.3: Test PHP Endpoint

```bash
curl -X POST https://yourdomain.com/worker/web_shim.php \
  -H "Content-Type: application/json" \
  -d '{"test": true}'
# Expected: {"error": "Invalid request: missing payload or signature"}
```

### Step 5.4: Update Frontend Environment

In Vercel or your frontend hosting, add:

```
NEXT_PUBLIC_DREAMHOST_WORKER_URL=https://yourdomain.com/worker
```

Redeploy the frontend.

---

## Phase 6: Disable PythonAnywhere Scheduler (Optional)

Once you've confirmed DreamHost workers are running correctly, you can disable the PA scheduler:

Edit `backend/run_tasks.py` and comment out the scraping/digest calls, or simply don't schedule the PA task.

---

## Verification Checklist

- [ ] `curl https://your-pa.pythonanywhere.com/api/worker/sources` returns 401
- [ ] `./run.sh run_scrapers.py` completes without errors
- [ ] `./run.sh run_mailer.py` completes without errors
- [ ] Cron jobs appear in `crontab -l`
- [ ] Check `~/logs/scraper.log` after 6 hours
- [ ] Check `~/logs/mailer.log` after 8 AM
- [ ] (Optional) Test email button works in admin panel

---

## Troubleshooting

### "Invalid worker signature" error

1. Verify `WORKER_SECRET` is identical on both PA and DH
2. Check server time sync (signature has 5-minute window)
3. Ensure `.env` is being sourced correctly

### Scraper returns no sources

1. Check sources are approved in PA database (`is_approved=True`)
2. Verify PA_API_URL is correct (no trailing slash)

### Emails not sending

1. Test SMTP credentials:
   ```bash
   python -c "
   import smtplib
   s = smtplib.SMTP('mail.yourdomain.com', 587)
   s.starttls()
   s.login('user', 'pass')
   print('SMTP OK')
   "
   ```
2. Check DreamHost mail logs: `~/logs/maillog`

### PHP shim signature mismatch

1. Verify `SECRET_KEY` in `.htaccess` matches Flask's SECRET_KEY exactly
2. Check PHP error logs: `~/logs/yourdomain.com/error.log`

---

## Security Notes

1. **Never commit secrets to git** - use environment variables
2. **WORKER_SECRET** authenticates DreamHost→PythonAnywhere communication
3. **SECRET_KEY** is used for signing test email payloads (browser→DreamHost)
4. Both use HMAC-SHA256 with timing-safe comparison
5. Timestamps prevent replay attacks (5-10 minute windows)
