# DaedalusSignal User Demo Scenarios

This guide covers key user scenarios for demonstrating DaedalusSignal's features.

---

## Prerequisites

1. Start the application using `.\startup.ps1` from the `_docs` folder
2. Access the frontend at http://localhost:3000
3. The frontend connects to the production API at https://signal.daedalusapps.com/api by default

---

## Scenario 1: New User Registration & Onboarding

**Goal:** Show how a new user signs up and completes initial setup.

### Steps
1. Navigate to http://localhost:3000
2. Click "Get Started" or "Sign Up"
3. Enter email and password to create an account
4. Complete the onboarding wizard:
   - Select initial topics/tags of interest
   - Add initial content sources
   - Configure digest preferences

### Demo Points
- Highlight the simple registration flow
- Show the curated default tags for agentic development topics
- Demonstrate source validation

---

## Scenario 2: Managing Content Sources

**Goal:** Demonstrate adding and managing content sources from multiple platforms.

### Steps
1. Log in and navigate to **Dashboard > Sources**
2. Add sources from supported platforms:
   - **YouTube**: Add a channel URL (e.g., AI/ML focused channels)
   - **X (Twitter)**: Add an account handle
   - Note: GitHub and LinkedIn are shown in the UI as disabled "future feature" options and are not currently supported
3. Show the source limit (10 sources per user)
4. Edit or remove an existing source

### Demo Points
- Platform icons and visual differentiation
- Source validation feedback
- Easy add/remove workflow

---

## Scenario 3: Customizing Tags & Keywords

**Goal:** Show how users personalize content filtering with tags.

### Steps
1. Navigate to **Dashboard > Tags**
2. View existing tags (default topics)
3. Add custom tags:
   - "context engineering"
   - "agentic workflows"
   - "LLM tooling"
4. Remove or modify tags
5. Show the tag limit (20 tags per user)

### Demo Points
- Keyword and semantic filtering explanation
- How tags influence the relevance score
- Tag management interface

---

## Scenario 4: Browsing the Content Feed

**Goal:** Demonstrate the core value - curated, high-signal content.

### Steps
1. Navigate to **Dashboard > Feed**
2. Show content cards with:
   - Title and description
   - Source platform icon
   - Relevance score (percentage)
   - Content type label
3. Filter content by platform:
   - Click "All" / "X" / "YouTube" filters (LinkedIn/GitHub filters are shown disabled - future feature)
4. Click on a content card to open the original source

### Demo Points
- Relevance scoring system
- Visual platform differentiation (colors, icons)
- Clean, scannable layout
- Direct links to original content

---

## Scenario 5: Email Digest Configuration

**Goal:** Show the daily digest feature and opt-out capability.

### Steps
1. Navigate to **Dashboard > Digest**
2. Show current digest settings:
   - Digest enabled/disabled toggle
   - Email preferences
3. Toggle digest on/off
4. Explain digest timing (8:00 AM daily)

### Demo Points
- Opt-out respect for user preferences
- Daily summary of top content
- No spam - one email per day max

---

## Scenario 6: Admin Panel (Admin Users Only)

**Goal:** Demonstrate admin capabilities for managing defaults.

### Prerequisites
- Logged in as an admin user

### Steps
1. Navigate to **Dashboard > Admin** (only visible to admins)
2. Manage default sources:
   - Add/remove default sources for new users
3. Manage default tags:
   - Add/remove default tags for new users
4. View system statistics

### Demo Points
- Admin badge visible in sidebar
- Centralized management of defaults
- Affects new user onboarding experience

---

## Scenario 7: Logout & Session Management

**Goal:** Show secure session handling.

### Steps
1. Click "Logout" button in the sidebar
2. Show redirect to landing page
3. Attempt to access dashboard directly - show redirect to login

### Demo Points
- Secure session management
- Clean logout flow
- Protected routes

---

## Quick Demo Flow (5 minutes)

For a fast demo, follow this condensed flow:

1. **Landing Page** (30s): Show value proposition
2. **Login** (15s): Quick authentication
3. **Feed** (2min): Browse content, show filters and relevance scores
4. **Sources** (1min): Add a new YouTube source
5. **Tags** (45s): Add a custom tag
6. **Digest** (30s): Toggle email preferences

---

## API Demo Endpoints

For technical demos, show these API endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/auth/me` | GET | Current user info |
| `/api/content/feed` | GET | Curated content feed |
| `/api/sources` | GET/POST | Manage sources |
| `/api/tags` | GET/POST | Manage tags |

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "No content yet" in feed | Add sources and wait for ingestion (runs every 6 hours) |
| Cannot access admin panel | Ensure user has `is_admin: true` in database |
| API not responding | Check `NEXT_PUBLIC_API_URL` and that the PHP API (production or a local `php -S` instance) is reachable |
| Frontend not loading | Check frontend is running on port 3000 |
