# Summary Python Backend

FastAPI backend for the mobile summary app. Text summarization uses a local heuristic summarizer, and audio transcription uses Gemini's dedicated `gemini-3.5-transcribe` model.

## Current Status

| Endpoint | Status | Notes |
| --- | --- | --- |
| `GET /health` | Real | Returns service and version metadata |
| `POST /summarize` | Real | Generates a heuristic summary from the submitted text |
| `POST /usage/check` | Real | Reads local usage state from SQLite |
| `POST /usage/increment` | Real | Increments local usage state |
| `POST /usage/reset` | Real | Resets local usage state |
| `POST /transcribe` | Gemini | Returns a real transcript; requires a backend API key |

## Review Path

- Health, text summaries, and usage tracking work without external services
- Real audio transcription requires Gemini access; automated tests mock Gemini
- `pytest` covers health, summarization, usage tracking, and upload handling
- GitHub Actions CI runs the Python test suite on push and pull request events

## Configure Gemini

Copy `.env.example` to `.env` and set `GEMINI_API_KEY` there, or set the environment
variable on the server. The backend loads `.env` automatically; existing environment
variables take precedence. Never commit `.env` or put the key in the Flutter client.
The project number is not needed for API-key authentication.

```bash
cp .env.example .env
```

The default model is `gemini-3.5-transcribe`; `GEMINI_STT_MODEL` can override it.
Hindi and Gujarati requests also include an Indian English language hint for mixed
voice notes. Omitting `language` enables automatic language detection.

Audio is sent inline through the [Gemini Interactions API](https://ai.google.dev/gemini-api/docs/transcribe)
with interaction storage disabled. New uploads are not saved to the backend's
`data/uploads` directory. Existing files from the old prototype are not deleted.
This does not override Google's own data handling policies; free-tier content
can be used to improve Google's products. See [Gemini pricing and data handling](https://ai.google.dev/gemini-api/docs/pricing).

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

Transcription accepts AAC, M4A, MP3, WAV, OGG, WebM, and FLAC files up to 20 MiB.
A successful response has `status: "completed"`, `serviceMode: "gemini"`, and
the recognized `transcript`. Missing credentials return 503; empty/invalid audio
returns 422; unsupported file extensions return 415; oversized uploads return
413; Gemini quota errors return 429; provider timeouts return 504. Errors never
return a placeholder transcript or expose the API key.

## Production Gaps

- Evaluate real Hindi, Gujarati, and mixed-language recordings before claiming transcription quality
- Add authentication and user-scoped usage limits if the backend is exposed publicly
- Move usage state out of local SQLite if the app needs multi-user hosted deployment
