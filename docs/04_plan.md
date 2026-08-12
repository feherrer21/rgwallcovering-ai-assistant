# Build Plan

**Case:** L1_Case05_Open_Choice_Prototype
**Status:** draft — written before any implementation code
**Depends on:** `03_spec.md`

Nine phases. Ordered so that each one produces evidence the case asks for,
rather than leaving evidence-gathering to the end where it becomes
reconstruction.

Estimates are recorded so the final effort statement can compare estimate
against actual, including where I was wrong.

---

### Phase 0 — Context artifact and its controlled experiment · ~1.5 h

`CLAUDE.md` at the repo root: domain vocabulary, the trust-tier rule, the
project's conventions, and the standing instruction that no business fact may
be asserted without a tier-A or tier-B source.

The case requires before-and-after evidence of its effect. **The subject of
that experiment is fixed here, in advance: `agent_core/retrieval.py`.**
Chosen before seeing any result, because choosing afterwards is choosing the
flattering comparison. It is a fair subject — non-trivial (relevance floor,
tier propagation, metadata handling) and representative of the project's real
work.

Procedure: generate the module with no `CLAUDE.md` present and archive the
output verbatim; write `CLAUDE.md`; regenerate the same module from the same
request; diff and record what changed and what did not. Both versions are
committed to `docs/evidence/`, so the comparison can be disagreed with.

Honest expectation: some of the difference will be noise. That gets reported
too.

### Phase 1 — Corpus ingestion · ~3 h

Fetch, clean, chunk and embed the sources fixed in `02` §1.1. Title-prefixed
chunks, tier metadata, explicit deny-list for the broken Services page.

**Done when:** `data/index/` builds from scratch with one command, and the
ingested chunk count and per-source breakdown are recorded — the actual
count, not the blog's advertised 28.

### Phase 2 — Retrieval · ~2 h

Query embedding, cosine similarity, top-*k*, and the relevance floor. Returns
passages with tier and source, or nothing.

**Done when:** unit tests prove that a query below the floor returns empty and
that tier metadata survives ingestion → retrieval intact. The floor starts at
a deliberately naive value; calibrating it is phase 6, not now.

### Phase 3 — Agent · ~4 h

`run_turn()`, the two tools, the system prompt with the tier rules and the
untrusted-input rule, lead persistence.

**Done when:** a conversation can be held end to end from a Python REPL,
including a lead that lands in `data/leads.jsonl` with a usable summary.

### Phase 4 — Frontends · ~2.5 h

Streamlit demo importing `agent_core` directly. FastAPI wrapper written and
exercised locally, not deployed.

**Done when:** the demo is usable by someone who is not me, and `POST /chat`
returns the contract in `03` §5 against a local uvicorn.

### Phase 5 — Evaluation harness and baseline · ~3 h

The 30 fixed questions from `02` §2.2. Runner records reply, sources,
deferred flag, latency and tokens. Manual labelling against S1–S4.

**Done when:** a baseline score exists for all four criteria and is committed.
This is the number every later claim is measured against, so it is recorded
before any tuning — including if it is bad.

### Phase 6 — The measured improvement · ~2 h

Calibrate `RELEVANCE_FLOOR`. Sweep values, re-run the evaluation set at each,
record S1 and S2 at every point.

**Done when:** before state, change, after state, **and what got worse** are
all documented. The regression is expected and is part of the deliverable:
raising the floor should remove fabrications and should also push some
answerable questions into deferral. A result showing only improvement would
mean the measurement is not sensitive enough to be trusted.

### Phase 7 — Failure analysis · ~2 h

Run the adversarial cases A1–A5 plus anything phases 5 and 6 surfaced. For
each failure: the exact input, the exact wrong output, and the mechanical
cause — not "it struggles with ambiguity".

**Done when:** at least five named failures with named causes, including at
least one that remains unfixed with the reason it was not worth fixing.

### Phase 8 — AI output review · ~1.5 h

Review of what the model generated for me across intent, tests, security,
performance and maintainability, plus at least one error I caught and
corrected, with the commit that corrected it.

Not a phase so much as a discipline running through 1–4; phase 8 is where it
is written up. Errors are recorded **as they happen** — reconstructing them
afterwards produces the vague, flattering version.

### Phase 9 — Communicate · ~2 h

One stakeholder slide, a demo recording or transcript including a case handled
badly, and the declared-effort statement with what was cut and why.

---

## Critical path and risk

Phases 1 → 2 → 3 are strictly sequential. 4 can slip; the demo is a
presentation surface, not the deliverable.

**The largest risk is that phase 5 is skipped or rushed.** Without a committed
baseline, phase 6 has nothing to measure against and phase 7 becomes
speculation — and those two carry disproportionate weight in the assessment.
If time runs short, the cut comes from phase 4 (a rougher demo) and never
from 5, 6 or 7.

**Total estimate: ~23.5 h**, excluding the ~4 h already spent on the discarded
spike and this specification.
