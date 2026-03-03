# Critical Workflow Watchdog (v1)

Critical Workflow Watchdog is a lightweight autonomous monitoring agent for SMB teams.
It validates mission-critical frontend workflows and detects backend API failures before customers report them.

## Tech Stack

- Python 3.11+
- FastAPI
- Playwright
- PostgreSQL
- Redis

## Project Structure

```text
app/
  main.py
  config.py
  database.py
  models/
  schemas/
  services/
  agent/
  alerts/
  scheduler/
  workers/
main.py
```

## Getting Started

1. Create and activate a Python 3.11+ virtual environment.
2. Install dependencies:

   ```bash
   pip install -e .
   ```

3. Install Playwright browser binaries:

   ```bash
   playwright install chromium
   ```

4. Run the API:

   ```bash
   uvicorn main:app --reload
   ```

5. Run DB migrations:

   ```bash
   alembic upgrade head
   ```

6. Verify health endpoint:

   ```bash
   curl http://127.0.0.1:8000/health
   ```

Expected response:

```json
{"status":"ok"}
```
