# Report: FastAPI Server Startup Port Binding Issue

Date: 2026-01-26

## Root Cause
- Ports 8000 and 8001 are inside the Windows excluded port range `7998-8097` (shown by `netsh interface ipv4 show excludedportrange protocol=tcp`).
- Windows reserves these ranges (commonly for Hyper-V or system services), which triggers WinError 10013 when uvicorn attempts to bind.

## Solution Implemented
- Switched the backend to read host/port from environment variables and default to a non-reserved port.
- Updated `SERVER_PORT` in the backend `.env` to `5000`.

## Working Port
- `5000`

## Test Results
- Started server via `py main.py` and verified the health endpoint:
  - `GET http://127.0.0.1:5000/` -> `{"status":"ok","game":"AI Trial"}`

## Files Updated
- `ai-trial-game/backend/main.py`
- `ai-trial-game/backend/.env`
