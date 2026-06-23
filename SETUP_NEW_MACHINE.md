# Setting Up on a New Mac — Adamjee Demo

Complete step-by-step guide to get the platform running from scratch on a new macOS machine.

---

## Prerequisites

Install these first (if not already installed):

```bash
# 1. Homebrew (macOS package manager)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. Python 3.11
brew install python@3.11

# 3. Node.js 20
brew install node@20
echo 'export PATH="/opt/homebrew/opt/node@20/bin:$PATH"' >> ~/.zprofile
source ~/.zprofile

# 4. PostgreSQL 14
brew install postgresql@14
brew services start postgresql@14
echo 'export PATH="/opt/homebrew/opt/postgresql@14/bin:$PATH"' >> ~/.zprofile
source ~/.zprofile

# 5. WeasyPrint system libraries (for PDF generation)
brew install pango cairo libffi gdk-pixbuf

# 6. Redis (for caching — optional, app works without it)
brew install redis
brew services start redis
```

---

## Step 1 — Get the Code

Either:
- **From ZIP**: Unzip the folder to `~/Downloads/` (or anywhere you prefer)
- **From GitHub**: `git clone https://github.com/zeesakhan/multitenant.git`

```bash
# Navigate to the project
cd ~/Downloads/python-claude-health-insurance-platform-auuco
```

---

## Step 2 — Create the Database

```bash
# Find your macOS username
whoami
# (remember this — you need it in Step 3)

# Create the PostgreSQL database
createdb health_insurance

# Verify it was created
psql -d health_insurance -c "SELECT version();"
```

---

## Step 3 — Configure the Backend

```bash
cd backend

# Copy the demo env file
cp .env.demo .env

# Edit .env — replace YOUR_MAC_USERNAME with your actual username from Step 2
# Example: if whoami returns 'john', change:
#   DATABASE_URL=postgresql://YOUR_MAC_USERNAME@localhost:5432/health_insurance
# to:
#   DATABASE_URL=postgresql://john@localhost:5432/health_insurance

nano .env
# (or open in any text editor — just change the one line)
```

---

## Step 4 — Install Python Dependencies

```bash
# Still inside backend/
python3.11 -m venv venv
venv/bin/pip install -r requirements.txt
```

> This installs FastAPI, SQLAlchemy, WeasyPrint, and all other dependencies.
> Takes 2–3 minutes on first run.

---

## Step 5 — Run Database Migrations

```bash
# Still inside backend/
venv/bin/alembic upgrade head
```

> This creates all 26 tables. You should see migrations 0001 through 0026 run.

---

## Step 6 — Seed Adamjee Data

```bash
# Seed the base Adamjee tenant, admin user, 10 plans, and config
venv/bin/python main.py

# Seed the demo applications, policies, AML records, notifications
venv/bin/python scripts/seed_demo_adamjee.py
```

> You should see:
> ```
> ✅ Demo data seeded successfully!
>    Applications: 7 (Draft/Submitted/Approved/Issued/AML Hold)
>    Policies: 3 active (2 standard + 1 expiring soon)
>    Payments: AED 16,550 total collected
>    AML: 1 MEDIUM flagged, 1 HIGH hold
>    Notifications: 7 (4 unread)
> ```

---

## Step 7 — Install Frontend Dependencies

```bash
cd ../frontend
npm install
```

> Takes 1–2 minutes on first run.

---

## Step 8 — Start Both Services

Open **two terminal windows**:

**Terminal 1 — Backend:**
```bash
cd ~/Downloads/python-claude-health-insurance-platform-auuco
./start_backend.sh
```

**Terminal 2 — Frontend:**
```bash
cd ~/Downloads/python-claude-health-insurance-platform-auuco
./start_frontend.sh
```

---

## Step 9 — Verify Everything Works

Open a browser and check:

| URL | Expected |
|-----|---------|
| http://localhost:8001/health | `{"status":"ok"}` |
| http://localhost:5173 | Login page loads |
| http://localhost:8001/docs | Swagger API docs |

Login with:
- **Email**: `admin@adamjee.ae`
- **Password**: `adamjee123`

---

## LAN Access (Demo from Another Device)

Find your IP address:
```bash
ipconfig getifaddr en0
```

Then use `http://<YOUR_IP>:5173` on any device on the same Wi-Fi network.

---

## Troubleshooting

### PDF generation fails (500 error)
```bash
# Ensure pango/cairo are installed
brew install pango cairo gdk-pixbuf

# Restart the backend — it auto-loads the libraries
./start_backend.sh
```

### Database connection error
```bash
# Make sure PostgreSQL is running
brew services start postgresql@14

# Make sure the database exists
createdb health_insurance  # (safe to run again — fails silently if exists)

# Check your username in .env matches `whoami`
whoami
grep DATABASE_URL backend/.env
```

### Port already in use
```bash
# Kill anything on port 8001
lsof -ti:8001 | xargs kill -9

# Kill anything on port 5173
lsof -ti:5173 | xargs kill -9
```

### node command not found
```bash
export PATH="/opt/homebrew/opt/node@20/bin:$PATH"
# Then retry npm install
```

### Frontend shows blank page or 404 on API calls
Check that the backend is running on port **8001** (not 8000).

---

## Demo Login
| Field | Value |
|-------|-------|
| Email | admin@adamjee.ae |
| Password | adamjee123 |
| Tenant UUID | 84595acc-7561-4684-9aba-7a14795ec81d |

## Demo Data Summary
| Item | Count |
|------|-------|
| Applications | 7 (all lifecycle stages) |
| Active Policies | 3 |
| AML Alerts | 2 (MEDIUM + HIGH) |
| Unread Notifications | 4 |
| Total Premium Collected | AED 16,550 |
