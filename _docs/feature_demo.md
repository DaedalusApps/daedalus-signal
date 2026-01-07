# Feature Demo Guide

This guide explains how to test and demo the 4 new features.

## Prerequisites
- Backend running on localhost:5000 (or PythonAnywhere)
- Frontend running on localhost:3000 (or DreamHost)
- Admin account logged in

---

## Feature 0: Test Email Button

**Location:** Admin Dashboard → Overview tab

**Steps:**
1. Log in as admin
2. Navigate to `/dashboard/admin`
3. Click "Send Test Email" button
4. Check console output (if `EMAIL_MODE=console`) or inbox (if `EMAIL_MODE=smtp`)

**Expected Result:**
- Success message: "Test email sent to admin@example.com"
- If SMTP configured: Email arrives in admin inbox

---

## Feature 2: In-App Notifications

**Location:** Sidebar → Feed link

**Steps:**
1. Log in to dashboard
2. Note: First visit sets baseline (no badge)
3. Run content ingestion: `python run_scheduler.py`
4. Refresh page (don't go to Feed yet)
5. See notification badge on "Feed" link showing count

**Expected Result:**
- Badge shows number of new items (e.g., "5" or "99+")
- Click Feed → badge clears
- Badge uses localStorage key: `lastContentCheck`

**To Reset:**
```javascript
localStorage.removeItem('lastContentCheck');
location.reload();
```

---

## Feature 3: Delete Profile

### Admin Deleting Users
**Location:** Admin Dashboard → Users tab

**Steps:**
1. Log in as admin
2. Navigate to `/dashboard/admin` → Users tab
3. Click "Delete" next to a non-admin user
4. Confirm the deletion

**Expected Result:**
- User removed from list
- User can no longer log in

### User Self-Deletion (API Only)
Currently only accessible via API:

```bash
curl -X DELETE https://your-backend/api/auth/me \
  -H "Cookie: session=your-session-cookie"
```

---

## Feature 4: Unsubscribe Block List

### Testing Unsubscribe Link
**Steps:**
1. Generate a test unsubscribe URL:
   ```python
   from app.api.unsubscribe import generate_unsubscribe_token
   email = "test@example.com"
   token = generate_unsubscribe_token(email)
   print(f"/api/unsubscribe/{token}?email={email}")
   ```
2. Visit the URL in browser
3. See success message

**Expected Result:**
- Message: "test@example.com has been unsubscribed"
- Email added to blocklist

### Viewing/Managing Blocklist (Admin)
**Location:** API only (no UI yet)

```bash
# Get blocklist
curl https://your-backend/api/admin/blocklist \
  -H "Cookie: session=admin-cookie"

# Unblock an email
curl -X DELETE https://your-backend/api/admin/blocklist/1 \
  -H "Cookie: session=admin-cookie"
```

---

## Quick API Test Commands

```bash
# Health check
curl https://your-backend/api/health

# Test new-count endpoint (logged in)
curl "https://your-backend/api/content/new-count?since=2024-01-01T00:00:00Z" \
  -H "Cookie: session=your-session"

# Generate unsubscribe token (Python)
python -c "from app.api.unsubscribe import generate_unsubscribe_token; print(generate_unsubscribe_token('test@example.com'))"
```

---

## Notes

- **Email Mode:** Set `EMAIL_MODE=console` in `.env` to test without SMTP
- **Database:** Run `python seed.py` to create test data
- **Admin Account:** Uses `ADMIN_EMAIL` and `ADMIN_PASSWORD` from `.env`
