# B00 — Open-Source Self-Hosted Setup

> **Objective:** A new user clones the repo, adds their API key, runs one command, and has the backend running on their laptop. Their phone connects over local WiFi.

**Depends on:** Nothing (this is the project foundation)

---

## User Experience Goal

```text
Step 1:  git clone https://github.com/you/mathpath.git
Step 2:  cd mathpath
Step 3:  cp .env.example .env
Step 4:  Edit .env → paste ONE API key (OpenAI, Anthropic, or Gemini)
Step 5:  docker compose up
Step 6:  Open phone app → enter laptop IP → done
```

That's it. No cloud account, no deployment, no domain, no Kubernetes.

---

## Docker Compose — `docker-compose.yml`

```yaml
services:
  db:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_USER: mathpath
      POSTGRES_PASSWORD: mathpath
      POSTGRES_DB: mathpath
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U mathpath"]
      interval: 5s
      timeout: 3s
      retries: 5

  api:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    env_file:
      - .env
    environment:
      DATABASE_URL: postgresql://mathpath:mathpath@db:5432/mathpath
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - ./backend:/app
      - uploads:/app/uploads
    command: >
      sh -c "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

volumes:
  pgdata:
  uploads:
```

Key details:
- Uses `pgvector/pgvector:pg16` (Postgres with pgvector pre-installed — no manual extension setup).
- API binds to `0.0.0.0` so phones on the same network can reach it.
- `alembic upgrade head` runs automatically on startup.
- Volumes persist data across restarts.

---

## Backend Dockerfile — `backend/Dockerfile`

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## `.env.example`

```bash
# ============================================
# MathPath Configuration
# ============================================
# You only need ONE API key. Pick your provider.

# Option 1: OpenAI
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o
OPENAI_API_KEY=

# Option 2: Anthropic (uncomment and set provider)
# LLM_PROVIDER=anthropic
# LLM_MODEL=claude-sonnet-4-20250514
# ANTHROPIC_API_KEY=

# Option 3: Google Gemini (uncomment and set provider)
# LLM_PROVIDER=gemini
# LLM_MODEL=gemini-2.0-flash
# GEMINI_API_KEY=

# ============================================
# Advanced (usually no changes needed)
# ============================================
DATABASE_URL=postgresql://mathpath:mathpath@db:5432/mathpath
LOG_LEVEL=INFO
DEBUG=true
```

The env file is intentionally simple. A user pastes ONE key and they're done.

---

## How the Phone Connects

### Same WiFi network (most common)

```text
1. Laptop and phone are on the same WiFi.
2. Laptop's local IP: 192.168.1.42 (find via `ifconfig` / `ipconfig`).
3. Phone app settings: enter http://192.168.1.42:8000
4. App calls http://192.168.1.42:8000/api/health → {"status": "ok"}
5. Everything works.
```

### The mobile app needs a "Server URL" config

On first launch (before onboarding), the app shows:

```text
┌──────────────────────────────┐
│  Connect to MathPath Server  │
│                              │
│  Server URL:                 │
│  ┌────────────────────────┐  │
│  │ http://192.168.1.42:80 │  │
│  └────────────────────────┘  │
│                              │
│  [Find automatically]        │
│  Scans local network for     │
│  MathPath server             │
│                              │
│         [Connect]            │
│                              │
│  Status: ● Connected         │
└──────────────────────────────┘
```

Store the URL in AsyncStorage. Test connection by calling `/api/health`.

### Optional: Auto-discovery

The backend can broadcast via mDNS/Bonjour (nice-to-have, not MVP):

```python
# Backend advertises: _mathpath._tcp.local on port 8000
# Phone scans for it and auto-fills the URL
```

For MVP, manual IP entry is fine. The app should show clear instructions:
> "Run `docker compose up` on your computer, then enter your computer's IP address above."

---

## First-Run Experience

After `docker compose up`, the user's first interaction:

```text
Terminal output:
  ✓ Database ready
  ✓ Migrations applied
  ✓ MathPath API running at http://0.0.0.0:8000
  ✓ Your local IP: 192.168.1.42
  
  Open the MathPath app on your phone and enter:
  http://192.168.1.42:8000

  API docs: http://localhost:8000/docs
```

The startup script should **print the local IP** so the user doesn't have to find it manually.

### IP detection helper — `scripts/show_ip.py`

```python
import socket

def get_local_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    finally:
        s.close()
```

Call this on startup and print it in the uvicorn startup log.

---

## Non-Docker Setup (for developers)

```bash
# 1. Install Postgres with pgvector
brew install postgresql
# Or use Postgres.app on Mac

# 2. Create database
createdb mathpath

# 3. Enable pgvector
psql mathpath -c "CREATE EXTENSION IF NOT EXISTS vector;"

# 4. Setup Python env
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 5. Configure
cp .env.example .env
# Edit .env: set DATABASE_URL and your API key

# 6. Run migrations
alembic upgrade head

# 7. Start server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Files to Create

```text
docker-compose.yml          (project root)
backend/Dockerfile
.env.example                (project root)
scripts/show_ip.py
```

---

## Acceptance Criteria

- [ ] `docker compose up` starts Postgres + API from a clean clone + one API key.
- [ ] `GET http://localhost:8000/api/health` returns `{"status": "ok"}`.
- [ ] `GET http://<laptop-ip>:8000/api/health` works from phone browser.
- [ ] Startup log prints the local IP address.
- [ ] No manual SQL or migration commands needed — it's automatic.
- [ ] Works with ONLY an OpenAI key set (no Anthropic/Gemini needed).
- [ ] Works with ONLY an Anthropic key set (no OpenAI/Gemini needed).
- [ ] Works with ONLY a Gemini key set (no OpenAI/Anthropic needed).

---

## Agent Prompt

```text
Create the open-source self-hosted setup for MathPath:

1. docker-compose.yml at project root — two services: db (pgvector/pgvector:pg16) and api (built from backend/Dockerfile). API runs alembic upgrade head on start, binds to 0.0.0.0:8000. DB persists via volume.

2. backend/Dockerfile — Python 3.12, install requirements, expose 8000.

3. .env.example at project root — clearly commented with 3 provider options (user picks one and pastes one key). Include DATABASE_URL default pointing to Docker db service.

4. scripts/show_ip.py — detect and print local IP. Call on FastAPI startup event so it prints in the console.

5. Update app/main.py to print server URL with local IP on startup.
```
