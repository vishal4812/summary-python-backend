# Summary Python Backend

Prototype FastAPI backend for the mobile summary app. Text summarization now uses a real local heuristic summarizer, while audio upload is wired end to end but transcript generation is still placeholder until a speech-to-text provider is connected.

## Current Status

| Endpoint | Status | Notes |
| --- | --- | --- |
| `GET /health` | Real | Returns service and version metadata |
| `POST /summarize` | Real | Generates a heuristic summary from the submitted text |
| `POST /usage/check` | Real | Reads local usage state from SQLite |
| `POST /usage/increment` | Real | Increments local usage state |
| `POST /usage/reset` | Real | Resets local usage state |
| `POST /transcribe` | Prototype | Stores uploads correctly and returns a placeholder transcript |

## Review Path

- No external services are required for local review
- `pytest` covers health, summarization, usage tracking, and upload handling
- GitHub Actions CI runs the Python test suite on push and pull request events

## Run Locally

```bash
cd /home/addweb/Learning/Pro/04-prototypes-needing-work/summary-app/summary-python-backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8010
```

If you want to run the test suite locally:

```bash
pip install -r requirements-dev.txt
pytest
```

## Example Requests

```bash
curl http://127.0.0.1:8010/health
```

```bash
curl -X POST http://127.0.0.1:8010/summarize \
  -H 'Content-Type: application/json' \
  -d '{
    "text": "The app can upload voice notes, track free usage locally, and return readable summaries for review.",
    "language": "English",
    "mode": "short_bullets"
  }'
```

```json
{
  "success": true,
  "summary": "The app can upload voice notes, track free usage locally, and return readable summaries for review.",
  "bulletPoints": [
    "The app can upload voice notes, track free usage locally, and return readable summaries for review."
  ],
  "detailedSummary": "Auto-generated summary for the submitted English text.\n\n- The app can upload voice notes, track free usage locally, and return readable summaries for review.",
  "serviceMode": "heuristic"
}
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

## Production Gaps

- Replace the placeholder transcription response with a real speech-to-text provider
- Add authentication and user-scoped usage limits if the backend is exposed publicly
- Move usage state out of local SQLite if the app needs multi-user hosted deployment
