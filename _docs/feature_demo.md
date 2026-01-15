# Feature Demo Guide

This guide explains how to test and demo the features.

## Prerequisites
- Frontend running on localhost:3000 (or DreamHost)
- API running at https://signal.daedalusapps.com/api (or local PHP)
- Admin account logged in

---

## Feature 0: Test Email Button

**Location:** Admin Dashboard → Overview tab

**Steps:**
1. Log in as admin
2. Navigate to `/dashboard/admin`
3. Click "Send Test Email" button
4. Check inbox for test email

**Expected Result:**
- Success message: "Test email sent to admin@example.com"
- Email arrives in admin inbox

---

## Feature 2: In-App Notifications

**Location:** Sidebar → Feed link

**Steps:**
1. Log in to dashboard
2. Note: First visit sets baseline (no badge)
3. Wait for scraper cron job to run (or trigger manually)
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
curl -X DELETE https://signal.daedalusapps.com/api/auth/me \
  -H "Authorization: Bearer your-jwt-token"
```

---

## Feature 4: Unsubscribe Block List

### Testing Unsubscribe Link
Unsubscribe links are included in digest emails. The URL format is:
```
/api/unsubscribe/{token}?email={email}
```

**Expected Result:**
- Message: "test@example.com has been unsubscribed"
- Email added to blocklist

### Viewing/Managing Blocklist (Admin)
**Location:** API only (no UI yet)

```bash
# Get blocklist
curl https://signal.daedalusapps.com/api/admin/blocklist \
  -H "Authorization: Bearer admin-jwt-token"

# Unblock an email
curl -X DELETE https://signal.daedalusapps.com/api/admin/blocklist/1 \
  -H "Authorization: Bearer admin-jwt-token"
```

---

## Quick API Test Commands

```bash
# Health check
curl https://signal.daedalusapps.com/api/health

# Test new-count endpoint (logged in)
curl "https://signal.daedalusapps.com/api/content/new-count?since=2024-01-01T00:00:00Z" \
  -H "Authorization: Bearer your-jwt-token"
```

---

## Notes

- **Database Seeding:** Run `php api/seed.php` to create default data
- **Admin Account:** Uses credentials set in API `.htaccess`
