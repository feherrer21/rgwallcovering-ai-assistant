# Declared effort — estimated, actual, and what was cut

## The numbers

The plan estimated **~25 h**, excluding roughly 4 h already spent on a
discarded spike and the specification before the repository existed.

Actual, measured from commit timestamps rather than recalled:

| Session | Span | Elapsed | What was built |
|---|---|---|---|
| 1 | 2026-08-12 18:44 → 00:23 | **5 h 39** | Spec commits, phases 0–3, phase 4.5 |
| 2 | 2026-08-13 07:34 → 14:00 | **6 h 26** | Phase 4 + deployment, phases 5, 6, 7, 9 |
| | | **≈ 12 h** | plus ~4 h before the repo existed |

**≈ 16 h against a 25 h estimate.** Per phase, from the spans between commits:

| Phase | Estimated | Elapsed | Note |
|---|---|---|---|
| 0 · Context artifact | 1.5 h | 1 h 15 | |
| 1 · Ingestion | 3 h | 1 h 25 | |
| 2 · Retrieval | 2 h | 12 min | Cosine over numpy is genuinely small |
| 3 · Agent | 4 h | 1 h 43 | |
| 4.5 · Lead delivery | 1.5 h | 22 min | |
| 4 · Frontends | 3 h | 2 h 34 | Includes the Streamlit Cloud deployment, which was not in the plan |
| 5 · Evaluation | 3 h | 20 min + 5 min of runtime | The harness was quick; labelling 30 cases by hand was most of it |
| 6 · Measured improvement | 2 h | 2 h 07 | Six full runs at ~5 min each |
| 7 · Failure analysis | 2 h | 26 min | Cheap *because* phases 5 and 6 had already produced the failures |
| 9 · Communicate | 2 h | ~35 min | |

**The estimate was wrong in an interesting direction.** The phases that came in
fastest — 2, 5, 7 — were fast because earlier work had already produced their
inputs: the evaluation harness made failure analysis a reading exercise, and
the spec made retrieval a 250-line module. The phase that overran its shape
was 4, and only because deploying to Streamlit Cloud was added mid-flight and
was never in the plan.

**Two caveats, so the numbers are not read as more than they are.** Commit
spans measure elapsed session time, not focused hours — thinking time between
commits is included, and the five specification documents were written before
the repository existed, so their 10-minute span understates them badly. And
`04_plan.md`'s own note about ~4 h of prior work is an estimate, not a
measurement.

## Money

**≈ $5 of API spend**, of which **$3.63 is accounted for exactly**: ten
evaluation runs, all committed, at `claude-opus-5` list prices ($5/MTok in,
$25/MTok out). The rest is development conversations, the demo, and cache
traffic the harness does not count.

A full 30-question run costs **$0.48**, and **$0.37** after the phase 6 change
— the deterministic pre-retrieval cut input tokens by a third, which is the
most concrete result of that phase. A single conversation costs a few cents.

## What was cut, and why

**Cut before starting, in the spec:**

| Cut | Why |
|---|---|
| **Design inspiration from the portfolio** | The most attractive of the three original ideas, and cut deliberately: the 84 portfolio images carry no titles, styles or materials, so there is nothing to match a visitor's stated style against. Doing it properly needs Ronald to tag his own work first. Shipping a gesture at it would have been the "works on three hand-picked inputs" demo the case warns about |
| **Portkey gateway** (suggested in the brief) | A genuine loss — it would have given observable cost and latency in production. Cut for time; the evaluation harness records latency and token counts instead, which covers the measurement need but not the operational one |
| **Streaming responses** | Better perceived latency, but adds SSE handling to every consumer. The API contract is additive, so this can be added later without breaking anything. The cost is visible: 5–13 s of still screen per turn |
| **n8n, fine-tuning, a vector database, migrating the WordPress site** | Each rejected with its reason in `03_spec.md` §9. 28 blog posts is far too little to fine-tune on, and ~300 chunks does not need a database |

**Cut during the build:**

- **`GET /leads` as a usable endpoint.** Implemented behind a token and
  returning 503 without one, rather than shipped as a feature. The system of
  record is Ronald's inbox; an endpoint serving personal data was not worth
  keeping alive for convenience.
- **A second labeller for the evaluation set.** Not available. The bias is
  declared in `02` §2.3 rather than mitigated: the same person wrote the
  prompt, the questions and the labels.
- **Fixing `Q-02`**, the enquiry that is sometimes never registered. Named,
  reproduced, cause identified, and left for the next change so that phase 7's
  one fix could be measured properly instead of two being changed at once.

**Not cut, though the plan expected it to be:** per-IP rate limiting. The plan
listed it as a likely casualty; it shipped in T4.6, because `/chat` spends
Ronald's API budget and an unlimited endpoint is an open invoice against him.

## What the time actually bought

The two phases the brief weights most heavily — the data and the failure
analysis — cost 2 h 33 between them, and only because the 3 h spent on the
evaluation harness and the baseline came first. **The baseline was committed
before any tuning, including the criterion it fails** (S1 at 80% against a 90%
target), which is what makes every later claim on this project checkable
rather than asserted.

The single most valuable hour available on this project is still not mine to
spend: it is Ronald answering five questions, each of which converts a
deferral into a real answer at zero engineering cost.
