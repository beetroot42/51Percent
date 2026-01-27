# Setup Guide

## 1. Install Dependencies

```bash
cd ai-trial-game
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
pip install -r backend/requirements.txt
```

## 2. Configure Environment

```bash
copy backend/.env.example backend/.env
```

Edit `backend/.env` and set:
- `OPENAI_COMPATIBLE_API_KEY`
- `OPENAI_COMPATIBLE_BASE_URL` (must end at `/v1`)
- `OPENAI_COMPATIBLE_MODEL`

## 3. Run

```bash
python start.py
```

Open:
- http://localhost:5000/game
