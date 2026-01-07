# Deploying Daedalus Signal

This guide covers deploying the Flask backend to **PythonAnywhere** and the Next.js frontend to **DreamHost**.

## Architecture

| Component | Host | URL |
|-----------|------|-----|
| Frontend (Static) | DreamHost | `signal.daedalusapps.com` |
| Backend API | PythonAnywhere | `<username>.pythonanywhere.com` |
| Database | PythonAnywhere | MySQL (included) |

---

## Part 1: Backend on PythonAnywhere

### 1. Create a Web App
1. Log in to [PythonAnywhere](https://www.pythonanywhere.com)
2. Go to **Web** tab → **Add a new web app**
3. Choose **Flask** and select **Python 3.10** (or latest)
4. Note the default path: `/home/<username>/mysite/`

### 2. Upload Code
**Option A: Git Clone (Recommended)**
```bash
# In PythonAnywhere Bash console
cd ~
git clone https://github.com/DaedalusApps/daedalus-signal.git
```

**Option B: Upload ZIP**
- Use the **Files** tab to upload and extract

### 3. Set Up Virtual Environment
```bash
cd ~/daedalus-signal/backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install mysqlclient
```

### 4. Configure WSGI
1. Go to **Web** tab → click on your **WSGI configuration file** link
2. Replace contents with:

```python
import sys
import os

# Add your project to the path
project_home = '/home/<username>/daedalus-signal/backend'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Load environment variables
from dotenv import load_dotenv
load_dotenv(os.path.join(project_home, '.env'))

# Import Flask app
from app import create_app
application = create_app()
```

3. Update `<username>` with your PythonAnywhere username

### 5. Set Virtual Environment Path
In **Web** tab → **Virtualenv** section:
```
/home/<username>/daedalus-signal/backend/venv
```

### 6. Create MySQL Database
1. Go to **Databases** tab
2. Create a MySQL database (e.g., `<username>$daedalus`)
3. Note the hostname: `<username>.mysql.pythonanywhere-services.com`

### 7. Configure Environment
Create `/home/<username>/daedalus-signal/backend/.env`:

```ini
SECRET_KEY=your-secure-random-key
DATABASE_URL=mysql://<username>:<db_password>@<username>.mysql.pythonanywhere-services.com/<username>$daedalus

# Email (optional)
EMAIL_MODE=console
# EMAIL_MODE=smtp
# SMTP_HOST=smtp.example.com
# SMTP_PORT=587
# SMTP_USER=user@example.com
# SMTP_PASSWORD=password

# Admin credentials
ADMIN_EMAIL=admin@daedalusapps.com
ADMIN_PASSWORD=secure_password

# CORS
CORS_ORIGIN_1=https://signal.daedalusapps.com
```

### 8. Initialize Database
```bash
cd ~/daedalus-signal/backend
source venv/bin/activate
python seed.py
```

### 9. Reload Web App
Click **Reload** button in the **Web** tab.

### 10. Set Up Scheduled Task
Go to **Tasks** tab and add:

**For Free Tier (1 task only):**
| Time | Command |
|------|---------|
| Daily at 08:00 | `/home/<username>/daedalus-signal/backend/venv/bin/python /home/<username>/daedalus-signal/backend/run_tasks.py` |

This combined script runs both content ingestion AND the daily digest check.

**For Paid Tier (multiple tasks):**
| Time | Command |
|------|---------|
| Every 6 hours | `.../venv/bin/python .../run_scheduler.py` |
| Daily at 08:00 | `.../venv/bin/python .../run_digest.py` |

---

## Part 2: Frontend on DreamHost

### 1. Build for Production
On your local machine:

1. Create `frontend/.env.production`:
```ini
NEXT_PUBLIC_API_URL=https://<username>.pythonanywhere.com
```

2. Build:
```bash
cd frontend
npm run build
```

This creates an `out/` folder with static files.

### 2. Upload to DreamHost
1. Create/configure `signal.daedalusapps.com` in DreamHost panel
2. Upload contents of `out/` folder to the domain directory via FTP or SFTP
3. Ensure `index.html` is in the root

### 3. Add .htaccess (Optional)
For clean URLs without 404 errors on refresh:

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

## Part 3: Verify

1. **API Health**: `https://<username>.pythonanywhere.com/api/health`
   - Should return: `{"status": "healthy"}`

2. **Frontend**: `https://signal.daedalusapps.com`
   - Should load the app

3. **Login**: Test authentication flow

---

## Troubleshooting

### CORS Errors
- Ensure `CORS_ORIGIN_1` in `.env` matches your frontend URL exactly
- Reload the web app after changes

### Database Connection Errors
- Check `DATABASE_URL` format
- Ensure MySQL database exists in PythonAnywhere

### Static Files Not Loading
- Check that `out/` folder contents (not the folder itself) are in the domain root
