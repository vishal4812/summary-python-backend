# Summary Python Backend

Quick-start local backend for the Flutter summary app.

## What is real right now

- `GET /health`
- `POST /usage/check`
- `POST /usage/increment`
- `POST /transcribe` for real file upload handling

## What is intentionally dummy right now

- `POST /summarize`

It always returns the same summary payload so the mobile app can be wired end to end first.

## Run locally

```bash
cd /home/addweb/Learning/Pro/summary-app/summary-python-backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Example requests

```bash
curl http://127.0.0.1:8000/health
```

```bash
curl -X POST http://127.0.0.1:8000/summarize \
  -H 'Content-Type: application/json' \
  -d '{"text":"Hello world","language":"English","mode":"short_bullets"}'
```
