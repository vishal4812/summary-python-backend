# Summary Python Backend

Quick-start local backend for the Flutter summary app.

## What is real right now

- `GET /health`
- `POST /usage/check`
- `POST /usage/increment`
- `POST /usage/reset`
- `POST /transcribe` for real file upload handling

## What is intentionally dummy right now

- `POST /summarize`

It always returns the same summary payload so the mobile app can be wired end to end first.

## What is intentionally placeholder right now

- `POST /transcribe` writes the uploaded file and returns a placeholder transcript

This means the upload flow is real, but speech-to-text is not connected yet.

## Run locally

```bash
cd /home/addweb/Learning/Pro/summary-app/summary-python-backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8010
```

## Example requests

```bash
curl http://127.0.0.1:8010/health
```

```bash
curl -X POST http://127.0.0.1:8010/summarize \
  -H 'Content-Type: application/json' \
  -d '{"text":"Hello world","language":"English","mode":"short_bullets"}'
```

```bash
curl -X POST http://127.0.0.1:8010/usage/check \
  -H 'Content-Type: application/json' \
  -d '{"deviceId":"demo-device"}'
```

```bash
curl -X POST http://127.0.0.1:8010/transcribe \
  -F file=@/path/to/voice-note.wav \
  -F language=English
```
