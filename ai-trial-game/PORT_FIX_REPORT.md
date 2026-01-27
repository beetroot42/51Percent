# Port Conflict Fix Report

## Root Causes

1. Base URL pointed to the game server port (causing a loop)
2. The server port was already in use

## Fixes

- Validate `OPENAI_COMPATIBLE_BASE_URL` to ensure it does not point at the game server
- Add port availability checks before startup

## Result

The backend can start on an available port, and configuration errors are surfaced early.
