# Summary Python Backend

FastAPI backend for the mobile summary app. Text summarization uses Gemini `gemini-3.8-flash`, and audio transcription uses Gemini's dedicated `gemini-3.5-transcribe` model.

## Current Status

| Endpoint | Status | Notes |
| --- | --- | --- |
| `GET /health` | Real | Returns service and version metadata |
| `POST /summarize` | Real | Generates a validated Gemini summary in Hindi, Gujarati, or English |
| `POST /usage/check` | Real | Reads local usage state from SQLite |
| `POST /usage/increment` | Real | Increments local usage state |
| `POST /usage/reset` | Real | Resets local usage state |
| `POST /transcribe` | Gemini | Returns a real transcript; requires a backend API key |

## Review Path

- Health and usage tracking work without external services
- Text summaries and audio transcription require Gemini access; automated tests mock Gemini
- `pytest` covers health, summarization, usage tracking, and upload handling
- GitHub Actions CI runs the Python test suite on push and pull request events
- See the [2026-09-18 audio test report](docs/testing/2026-09-18.md) for live accuracy, format checks, and remaining gaps

## Configure Gemini

Copy `.env.example` to `.env` and set `GEMINI_API_KEY` there, or set the environment
variable on the server. The backend loads `.env` automatically; existing environment
variables take precedence. Never commit `.env` or put the key in the Flutter client.
The project number is not needed for API-key authentication.

### Keep Gemini on the free tier

An API key alone does not guarantee free usage: Gemini's tier is determined by the
Google project attached to that key. In [AI Studio Projects](https://aistudio.google.com/app/projects),
verify that the project is marked **Free** and offers **Set up billing**. Do not
attach a billing account or add prepaid credit if you require zero charges. Google
says disabling billing on a paid project downgrades it to the free tier; this
cannot be done or verified with the API key alone. A budget alert is not a
zero-cost guarantee. See [Gemini billing](https://ai.google.dev/gemini-api/docs/billing)
and [Google Cloud budget behavior](https://docs.cloud.google.com/billing/docs/how-to/budgets).

This backend uses only the configured Gemini transcription and summary models.
It neither enables billing nor changes models or retries automatically when a
quota is exhausted. A 429 is shown to the client and summary usage is not
incremented. During [live testing](docs/testing/2026-09-18.md), Google reported
`generate_content_free_tier_requests` for this project's summary quota, which is
evidence the tested requests were subject to free-tier limits at that time. If
billing is later enabled on the project, that observation will no longer prove
future calls are free. Stop the backend until the project's tier is verified.

```bash
cp .env.example .env
```

The transcription model defaults to `gemini-3.5-transcribe` (`GEMINI_STT_MODEL`).
The summary model defaults to `gemini-3.8-flash` (`GEMINI_SUMMARY_MODEL`).
Hindi and Gujarati requests also include an Indian English language hint for mixed
voice notes. Omitting `language` enables automatic language detection.

Audio and submitted transcript text are sent through the [Gemini Interactions API](https://ai.google.dev/gemini-api/docs/interactions)
with interaction storage disabled for both transcription and summaries. New uploads
are not saved to the backend's `data/uploads` directory. Existing files from the old prototype are not deleted.
This does not override Google's own data handling policies; free-tier content
can be used to improve Google's products. See [Gemini pricing and data handling](https://ai.google.dev/gemini-api/docs/pricing).

## Run Locally

```bash
cd /home/addweb/Learning/Pro/04-prototypes-needing-work/summary-app/summary-python-backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8010
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
  "detailedSummary": "The app supports voice-note uploads, local usage tracking, and readable summaries for review.",
  "serviceMode": "gemini"
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

## Summary Contract

`POST /summarize` accepts nonblank text up to 50,000 characters, a language of
`Hindi`, `Gujarati`, or `English`, and modes `short`, `short_bullets`, or `detailed`.
The existing `long_bullets` and `paragraph` modes remain supported. Defaults are
Hindi and short bullets. All responses contain `summary`, `bulletPoints`, and
`detailedSummary`; the selected mode controls the detail level and bullet limit.
Gemini is instructed to use the selected language's native script, preserve facts
and uncertainty, and treat transcript instructions as untrusted content.

The provider receives a JSON schema, and the backend validates the completed
response before returning it. Missing credentials or an unavailable model return
503, provider quota errors 429, timeouts 504, and malformed/incomplete responses or
other provider failures 502. Invalid input returns 422 before any provider call.
There is no silent heuristic fallback. Model-generated summaries can still
misinterpret source material and should be reviewed for accuracy.

The usage endpoints are separate: clients increment usage only after a successful
summary. This prototype does not yet enforce quotas within provider endpoints.

## Production Gaps

- Evaluate real Hindi, Gujarati, and mixed-language recordings before claiming transcription quality
- Add authentication and user-scoped usage limits if the backend is exposed publicly
- Move usage state out of local SQLite if the app needs multi-user hosted deployment
