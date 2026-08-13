# Technical Specification

**Case:** L1_Case05_Open_Choice_Prototype
**Status:** draft — written before any implementation code
**Depends on:** `01_problem_statement.md`, `02_data_provenance.md`

---

## 1. The decision the case forces: retrieval or n8n

The case requires **either** a retrieval pipeline over my own documents **or**
an n8n automation with AI in the loop, and requires a stated reason for
choosing one over the other.

**Chosen: retrieval.**

The problem in `01` is a *grounding* problem. Visitors ask questions the site
does not answer, and the expensive failure is an assistant that answers them
anyway. Retrieval is the mechanism that makes an answer traceable to a source,
and traceability is what makes success criterion S2 enforceable rather than
aspirational — a claim that cannot be traced to a retrieved passage is
detectable as a fabrication.

**Rejected: n8n**, for two reasons.

First, there is nothing to orchestrate. n8n earns its place when a workflow
spans several systems — CRM, email, calendar, Slack, a database. Here there is
exactly one destination for a lead and no CRM to route it to. An n8n workflow
would be a single node wrapping a single API call, which is orchestration
overhead in exchange for nothing.

Second, and decisively, it would not touch the actual problem. Automating lead
delivery makes a good answer arrive faster; it does nothing about whether the
answer was invented. Given a corpus that is thin exactly where visitors ask
(`02` §1.2), the risk being managed here is fabrication, not latency.

n8n becomes the right tool the moment Ronald has a CRM, or wants leads in
email plus a spreadsheet plus a notification. Recorded as a follow-on.

---

## 2. Architecture

```
                    demo_streamlit/          (demo UI, disposable)
                            │
                            ├──── direct import ────┐
                            │                       │
   WordPress widget ──HTTP──► backend/  ──import───►│
      (later)                (FastAPI)              │
                                                    ▼
                                             agent_core/
                                          (all logic, no HTTP)
                                                    │
                        ┌───────────────────────────┼───────────────┐
                        ▼                           ▼               ▼
                   retrieval.py                 tools.py        leads.py
                        │                           │
                  data/index/                  Claude API
              (built offline by ingest/)
```

`agent_core` knows nothing about HTTP, Streamlit or WordPress. Every frontend
is a consumer of the same `run_turn()`. This is what makes the eventual
WordPress integration a deployment task rather than a rewrite.

**Deployment for the prototype:** Streamlit imports `agent_core` directly. The
FastAPI wrapper is written and exercised locally but not deployed, because
deploying it buys nothing for the demonstration and costs a hosting
dependency. Recorded as a deliberate trade in `06_effort.md`.

---

## 3. Retrieval pipeline

### 3.1 Ingestion (offline, `agent_core/ingest/`)

Run manually; produces `data/index/`, which is gitignored and rebuildable.

1. **Fetch** the source list fixed in `02` §1.1. The broken Services page is
   excluded by an explicit deny-list, not by chance.
2. **Extract** text; discard navigation, footers and boilerplate.
3. **Chunk.** Target ~700 characters with ~120 character overlap, split on
   paragraph boundaries.
   **Every chunk carries its document title as a prefix.** A chunk that reads
   "…block printing was applied by hand…" is unidentifiable on its own; the
   same chunk prefixed with its title is attributable. This directly addresses
   the failure mode the case names — content severed from the heading that
   gave it meaning.
4. **Attach metadata** to every chunk: `source_id`, `tier` (A/B/C), `url`,
   `title`, `date`, `service_area` flag.
5. **Embed** and persist as a numpy matrix plus a JSONL of chunk records.

### 3.2 Store

A numpy array and a JSONL file. **No vector database.** The corpus is roughly
200–400 chunks; FAISS, Chroma or pgvector would be infrastructure with no
purpose at this size, and each would be a dependency to install, configure and
explain. Exact cosine similarity over a few hundred vectors is instant and has
no failure modes of its own. If the corpus grows an order of magnitude this
decision should be revisited — noted so the revisit is prompted by evidence
rather than fashion.

### 3.3 Embeddings

`fastembed` with `BAAI/bge-small-en-v1.5` — ONNX runtime, no PyTorch, no extra
API key, runs locally and free.

Rejected: Voyage AI (adds a second API credential and a per-query cost for a
prototype); `sentence-transformers` (drags in ~2 GB of PyTorch, which will not
fit comfortably on free-tier hosting).

### 3.4 The relevance floor — the crux of the design

Retrieval returns the top *k* chunks **only if** the best similarity clears a
threshold `RELEVANCE_FLOOR`. Below it, retrieval returns **nothing**, and the
agent is told plainly that nothing relevant exists.

This exists because of `02` §1.2. In a corpus of decorative essays, "how long
does installation take?" has a nearest neighbour — an article about cherry
blossoms — and a top-k retriever with no floor will return it with apparent
confidence. Everything downstream then looks like grounded generation and is
not.

`RELEVANCE_FLOOR` is a single tunable constant, and **calibrating it is the
project's designated measured improvement** (`04_plan.md`, phase 5). The
trade-off is expected to be visible and is expected to cost something:
raising the floor removes fabrications and will also push some genuinely
answerable questions into deferral. Both directions get reported.

### 3.5 Trust tiers as an enforcement mechanism

Each retrieved chunk carries its tier into the prompt:

- **A — first-party.** May be asserted as fact about the business.
- **B — third-party directory** (BBB, Houzz). May be asserted, but carries
  that it comes from a listing and may be out of date.
- **C — domain-general trade knowledge.** May be used to explain *what
  determines* an answer. May **never** be phrased as "we do X".

Tier C is what stops the corpus's thinness from making the assistant useless.
Asked how long installation takes, it can explain that duration is driven by
area, wall condition, whether old covering must come off, and whether the
pattern must be matched across seams — and then defer the actual number. That
is more useful than a fabricated figure and does not violate S2.

---

## 4. Agent

**Model:** `claude-opus-5`. **Effort:** `low` — a short conversational turn
over retrieved context does not need deep reasoning, and latency is visible to
the visitor. Adaptive thinking left on (the default): with tool use in the
loop, disabling thinking on this model risks tool calls being emitted as plain
text, which fails silently.

**Prompt caching** on the system block; it is byte-identical across every turn
of every conversation.

**Statelessness.** The frontend holds the conversation and sends it back. Only
text roles cross the boundary — tool-use blocks are resolved inside a turn and
never leave `agent_core`. This keeps the API contract trivial for a JavaScript
widget to consume.

### 4.1 Tools

| Tool | Purpose |
|---|---|
| `buscar_informacion` | Query the corpus. Returns passages with tier and source, or an explicit "nothing relevant found". |
| `registrar_lead` | Persist a structured lead plus the written summary for Ronald. |

Retrieval is a **tool the model calls**, not a step that always runs before
generation. Most conversational turns ("hi", "thanks", "my name is Ana") need
no retrieval at all, and forcing a search on every turn wastes latency and
invites irrelevant context into the prompt. The cost of this choice is that
the model may fail to search when it should — a named risk, tested by the
evaluation set.

### 4.2 Untrusted input

Both the visitor's message **and every retrieved passage** are untrusted data.
The system prompt states that instructions appearing inside either are content
to be reported, never commands to follow. Evaluation case A3 tests exactly
this.

---

## 5. API contract

```
POST /chat
  { "message": str, "history": [{role, content}], "conversation_id": str }
→ { "reply": str,
    "sources": [{title, url, tier}],
    "deferred": bool,
    "lead": {...} | null,
    "conversation_id": str }
```

`sources` and `deferred` are returned even though the demo UI barely renders
them: they are what makes grounding auditable from outside the process, and
they are what the evaluation runner scores against. A reply with
`deferred: false` and an empty `sources` array is, by construction, an
ungrounded answer.

```
GET /leads    → recent leads (dev only; removed or authenticated before any
                deployment — it exposes PII)
GET /health   → liveness
```

---

## 6. Storage and delivery

Two distinct concerns, previously conflated.

**Storage** — JSONL append-only at `data/leads.jsonl`, gitignored. This is a
local operational log, not the system of record.

**Delivery** — the lead is emailed to `info@rgwallcovering.com` the moment it
is captured: the structured fields and, above them, the written summary.

**The email is the system of record.** Ronald runs a five-person business and
already lives in that inbox; a database would mean a dashboard he has to
remember to check, and a CRM would mean an account he has to maintain. His
mail provider already gives durability, search, mobile access and a reply
button that reaches the customer. Building storage infrastructure alongside
that would be adding a worse copy of something he already has.

This also dissolves the ephemeral-disk problem in `02` §3.2 rather than
solving it: if the container restarts and `leads.jsonl` vanishes, nothing of
value is lost, because the lead left the process the moment it was created.

`leads.entregar()` is the seam. If Ronald later wants a spreadsheet or a CRM,
a second delivery target is added there and nothing else changes.

Failure handling: if delivery fails, the lead stays in the local JSONL and the
failure is logged loudly. The visitor is never told their details were lost —
they were not; they simply have not arrived yet.

---

## 7. Testing

- **Unit** (`pytest`): the relevance floor returns nothing below threshold;
  tier metadata survives ingestion → retrieval → prompt; lead records validate
  against the schema; chunking preserves the title prefix.
- **Evaluation harness** (`eval/`): runs the 30 fixed questions, records reply,
  sources, deferred flag and latency, and writes a scoreable table. Labelling
  is manual — S1 and S4 need human judgement — but the run is reproducible and
  the outputs are committed.

---

## 8. Security

- API key server-side only. `.env` gitignored from commit 1.
- CORS restricted to the client's origin in production; permissive locally.
- **The `/chat` endpoint spends money.** Unauthenticated and unlimited, it is
  an open invoice against Ronald's API budget. Since the target changed from
  demonstration to something he can actually run, **per-IP rate limiting moves
  from a named gap to a requirement** (T4.6). A prototype that never leaves
  localhost can defer this; one intended for his website cannot.
- `GET /leads` exposes PII. Removed or authenticated before deployment — with
  email delivery in place it is a development convenience, not a feature.
- Email credentials live in `.env` alongside the API key. A delivery failure
  must never surface the address or the credential in a response to the
  visitor.
- Prompt injection: §4.2.

---

## 9. Alternatives rejected

| Alternative | Why rejected |
|---|---|
| n8n instead of retrieval | §1. |
| Fine-tuning on the client's content | 28 blog posts is far too little; would bake facts into weights where they cannot be updated when Ronald answers the open questions. Retrieval keeps facts editable. |
| Streamlit monolith calling Claude directly | Fastest to demo, but recouples logic to the demo UI and would have to be undone for WordPress. `agent_core` costs nothing extra and removes that. |
| Vector database | §3.2. |
| Migrating the WordPress site | Independent problem. The blog and portfolio are Ronald's to edit himself; migrating means either a headless CMS (more work than this project) or making him depend on a developer to publish. Also risks the site's existing SEO for no benefit he would perceive. |
| Streaming responses | Better perceived latency, but adds SSE handling to every consumer. Deferred; the contract is additive, so adding it later breaks nothing. |
| Portkey gateway (suggested in the brief) | Would give observable cost and latency, and is a genuine loss. Cut for time; latency and token counts are recorded by the evaluation harness instead, which covers the measurement need if not the production one. |
