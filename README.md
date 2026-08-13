# RG Wallcovering assistant

A retrieval-grounded assistant for the website of **RG Wallcovering &
Painting, Inc.** (Providence, RI). It answers visitor questions from the
company's own published content, and when there is a real project behind the
questions it qualifies the enquiry and emails a written summary to the owner.

The design rule that shapes everything else: **it never states a fact about the
business that is not traceable to a source in the corpus** — no price, no
timeline, no warranty term, not even a hedged one. When retrieval finds
nothing, the assistant says so and offers to pass the enquiry to the team.
That is a correct outcome, not a failure.

Why the assistant defers so readily, and what the trust tiers mean, is in
[`docs/03_spec.md`](docs/03_spec.md). Problem, users and how success is
measured are in [`docs/01_problem_statement.md`](docs/01_problem_statement.md).

---

## Layout

```
agent_core/        all the logic; knows nothing about HTTP or Streamlit
  ingest/          offline pipeline: fetch → extract → chunk → embed
  retrieval.py     cosine similarity over a numpy array, with a relevance floor
  agent.py         run_turn(): the conversation loop
  leads.py         lead capture, and email delivery to the owner
backend/app/       thin FastAPI wrapper over agent_core
demo_streamlit/    disposable demo; imports agent_core directly, not the API
data/index/        the built index (generated, not committed)
docs/              spec, plan, evidence
```

## Setup

Python 3.11+.

```bash
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -r requirements.txt   # Windows
# source .venv/bin/activate && pip install -r requirements.txt  # macOS / Linux

cp .env.example .env        # then fill in ANTHROPIC_API_KEY
```

Build the index — needed once before anything will answer. It downloads the
site with a one-second courtesy pause between pages, so it takes a few minutes:

```bash
./.venv/Scripts/python.exe -m agent_core.ingest.build
```

Rebuild it whenever the sources, the chunking or the embedding model change.
Pages are cached under `data/cache/`, so a rebuild after the first run does not
hit the site again.

## Run it

**The demo** — chat, the passages behind each answer with their tier and score,
and the captured leads:

```bash
./.venv/Scripts/python.exe -m streamlit run demo_streamlit/app.py
```

**The API** — what the website would call:

```bash
./.venv/Scripts/python.exe -m uvicorn backend.app.main:app --reload --port 8000
```

```
POST /chat     { message, history, conversation_id }
             → { reply, sources[{title,url,tier}], deferred, lead, conversation_id }
GET  /health   liveness, plus whether the index loaded and email is configured
GET  /leads    recent leads — requires ADMIN_TOKEN; returns 503 without one
```

`sources` and `deferred` are in the response because they make grounding
auditable from outside the process: a reply with `deferred: false` and an empty
`sources` array is, by construction, an ungrounded answer. A worked transcript
of every endpoint is in
[`docs/evidence/api_transcript.md`](docs/evidence/api_transcript.md).

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "do you install wallpaper in Newport?"}'
```

## Tests

```bash
./.venv/Scripts/python.exe -m pytest tests/ -q
```

They never call the model and never send email — both are replaced by doubles.
Lead fixtures are invented people.

## Configuration

All of it lives in `.env`; defaults are in `agent_core/config.py`. See
`.env.example` for the annotated list. The ones that matter:

| Variable | Why you would touch it |
|---|---|
| `ANTHROPIC_API_KEY` | required |
| `SMTP_USER`, `SMTP_PASSWORD`, `LEAD_EMAIL_TO` | without these a lead is still captured to `data/leads.jsonl`, it just is not delivered |
| `ALLOWED_ORIGINS` | `*` while developing; **set it to the client's domain before deploying** |
| `ADMIN_TOKEN` | unset by default, which makes `GET /leads` return 503 |
| `RATE_LIMIT_POR_MINUTO`, `RATE_LIMIT_POR_HORA` | 10 and 60 per IP. `/chat` spends the owner's API budget |
| `RELEVANCE_FLOOR` | provisional at 0.62; calibrated against the evaluation set in phase 6 |

## Before this goes on a live site

- Set `ALLOWED_ORIGINS` to the client's domain.
- Leave `ADMIN_TOKEN` unset unless something actually needs `/leads`. The
  system of record is the owner's inbox, not that endpoint.
- The rate limiter keys on the socket address and ignores `X-Forwarded-For`,
  which cannot be trusted from the open internet. Behind a reverse proxy every
  visitor would share one bucket, so the proxy has to do the limiting or the
  real client IP has to be resolved there first.
- `data/leads.jsonl` holds personal data. It is gitignored, and conversation
  transcripts are never persisted — only the structured lead and its summary.

## Conventions

Comments and docstrings are in Spanish; everything the visitor reads is in
English. Contributor notes and the standing context for writing code here are
in [`CLAUDE.md`](CLAUDE.md); current status is in
[`docs/PROGRESS.md`](docs/PROGRESS.md).
