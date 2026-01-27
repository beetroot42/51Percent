# Quick Fix: Port In Use

## Symptoms

```
ERROR: [Errno 10048] error while attempting to bind on address ('0.0.0.0', 5000)
```

## Fix

1. Ensure the LLM base URL does not point to the game server port.
   ```env
   OPENAI_COMPATIBLE_BASE_URL=https://api.example.com/v1
   ```
2. Stop the process using the port.
   - Windows:
     ```powershell
     netstat -ano | findstr :5000
     taskkill /PID <PID> /F
     ```
   - Linux/Mac:
     ```bash
     lsof -ti :5000 | xargs kill -9
     ```
3. Restart the server:
   ```bash
   python start.py
   ```

## Alternative

Change the port in `backend/.env`:
```env
SERVER_PORT=5001
```
