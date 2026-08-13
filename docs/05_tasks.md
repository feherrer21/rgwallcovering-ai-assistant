# Task Breakdown

**Case:** L1_Case05_Open_Choice_Prototype
**Status:** draft — written before any implementation code
**Depends on:** `04_plan.md`

IDs are stable and referenced from commit messages, so the link from task to
implementation is visible in history.

---

## Phase 0 — Context artifact

- [ ] **T0.1** Generate `agent_core/retrieval.py` with **no** `CLAUDE.md`
      present. Archive verbatim to `docs/evidence/retrieval_before.py` with
      the exact prompt used.
- [ ] **T0.2** Write `CLAUDE.md`: project purpose, trust-tier rule, the
      no-unsourced-business-facts standing instruction, conventions
      (Spanish comments, English user-facing strings), and the pointer to
      `03_spec.md` as the source of design decisions.
- [ ] **T0.3** Regenerate `retrieval.py` from the identical prompt with
      `CLAUDE.md` present. Archive to `docs/evidence/retrieval_after.py`.
- [ ] **T0.4** Diff and write `docs/evidence/context_artifact_effect.md`:
      what changed, what did not, and which differences are plausibly noise.

## Phase 1 — Ingestion

- [ ] **T1.1** `agent_core/ingest/sources.py` — the source registry from
      `02` §1.1, with tier per source and the deny-list containing the broken
      Services page.
- [ ] **T1.2** Fetcher with local caching, so re-runs do not re-hit the
      client's site.
- [ ] **T1.3** HTML → text extraction; strip nav, footer, boilerplate.
- [ ] **T1.4** Chunker: ~700 chars, ~120 overlap, paragraph boundaries,
      **title prefixed into every chunk**.
- [ ] **T1.5** Author the tier-C trade-knowledge documents: what drives
      installation duration, what drives cost, what wall preparation involves,
      what a site visit is normally for, why quotes are per-project.
      Written as general domain knowledge, never as client policy.
- [ ] **T1.6** Embed with `fastembed` / `bge-small-en-v1.5`; persist matrix +
      chunk JSONL to `data/index/`.
- [ ] **T1.7** Record the actual ingested counts per source in
      `docs/evidence/corpus_stats.md`, and resolve the 28-vs-27 blog post
      discrepancy from `02` §1.3.

## Phase 2 — Retrieval

- [ ] **T2.1** `retrieval.py`: query embedding, cosine, top-*k*.
- [ ] **T2.2** `RELEVANCE_FLOOR` — return empty below threshold. Naive initial
      value; calibrated in T6.
- [ ] **T2.3** Return tier, title, url and score with every passage.
- [ ] **T2.4** `tests/test_retrieval.py`: below-floor returns empty; tier
      survives the round trip; title prefix present in chunks; empty corpus
      does not crash.

## Phase 3 — Agent

- [ ] **T3.1** `prompts.py` — system prompt: role, tier rules, deferral as a
      first-class outcome, untrusted-input rule, qualification flow, the
      `resumen` specification.
- [ ] **T3.2** `tools.py` — `buscar_informacion`, `registrar_lead`, dispatcher.
- [ ] **T3.3** `leads.py` — JSONL persistence, schema, `listar()`.
- [ ] **T3.4** `agent.py` — `run_turn()`, tool loop with iteration cap,
      `refusal` handling, prompt caching on the system block.
- [ ] **T3.5** `tests/test_leads.py` — schema validation, PII never logged.
- [ ] **T3.6** Manual end-to-end conversation from a REPL; confirm a lead
      lands with a usable summary.

## Phase 4 — Frontends

- [ ] **T4.1** `demo_streamlit/app.py` — chat UI, session history, sources
      panel, leads tab.
- [ ] **T4.2** `backend/app/main.py` — FastAPI, `POST /chat`, `GET /health`,
      `GET /leads`, CORS.
- [ ] **T4.3** Exercise the API locally with curl against the contract in
      `03` §5; record the transcript as evidence it was tested.
- [ ] **T4.4** `README.md` — setup, how to run both, how to rebuild the index.

## Phase 4.5 — Lead delivery

- [ ] **T4.5.1** `leads.entregar()` — email the lead to
      `info@rgwallcovering.com`. Summary first, structured fields under it,
      plain text. Subject line carries name and residential/commercial so it
      is triageable from a phone lock screen.
- [ ] **T4.5.2** Wire delivery into `registrar_lead` so capture and delivery
      are one step. A lead that is stored but not sent is a lost customer.
- [ ] **T4.5.3** Failure handling: delivery failure is logged loudly, the lead
      is retained in the local JSONL, and the visitor is **not** told anything
      went wrong — their details are not lost, only delayed.
- [ ] **T4.5.4** End-to-end test: capture a lead in conversation, confirm
      arrival in a real inbox, restart the process, confirm nothing is lost.
- [ ] **T4.5.5** Ask Ronald to confirm the destination address, and whether he
      wants painting enquiries through the same channel.
- [ ] **T4.6** Per-IP rate limiting on `POST /chat`. Now a requirement rather
      than a named gap, because the endpoint spends Ronald's API budget.

## Phase 5 — Evaluation

- [ ] **T5.1** `eval/questions.yaml` — the 30 questions, categorised per
      `02` §2.2, including A1–A5 verbatim.
- [ ] **T5.2** `eval/run.py` — execute all questions, record reply, sources,
      deferred, latency, tokens; write results as CSV/JSON.
- [ ] **T5.3** Label the baseline run manually against S1–S4.
- [ ] **T5.4** Commit `docs/evidence/baseline_results.md` **before** any
      tuning, whatever the numbers say.

## Phase 6 — Measured improvement

- [ ] **T6.1** Sweep `RELEVANCE_FLOOR` across a value range; re-run the
      evaluation set at each.
- [ ] **T6.2** Plot or tabulate S1 against S2 across the sweep.
- [ ] **T6.3** Choose a value and justify the choice in terms of the S2 hard
      gate, not overall average score.
- [ ] **T6.4** `docs/evidence/measured_improvement.md` — before, change,
      after, **and the regression**: which previously-answered questions now
      defer.

## Phase 7 — Failure analysis

- [ ] **T7.1** Run A1–A5; record exact input, exact output, mechanical cause.
- [ ] **T7.2** Collect every failure surfaced in phases 5 and 6.
- [ ] **T7.3** Fix one; measure the effect; report anything it broke.
- [ ] **T7.4** `docs/07_failure_analysis.md` — at least five named failures,
      including one left unfixed with the reason.

## Phase 8 — AI output review

- [ ] **T8.1** Keep `docs/evidence/ai_review_log.md` open from T1.1 onward;
      record errors as they happen, not afterwards.
- [ ] **T8.2** Write up intent / tests / security / performance /
      maintainability.
- [ ] **T8.3** Name at least one error caught and corrected, with the fixing
      commit hash.

## Phase 9 — Communicate

- [ ] **T9.1** One stakeholder slide, addressed to Ronald, not to an assessor.
- [ ] **T9.2** Demo transcript, **including a case handled badly** — required,
      not optional. Transcript rather than recording: the checklist accepts
      either, and the time goes to phase 4.5 instead.
- [ ] **T9.3** `docs/06_effort.md` — hours estimated vs actual, what was cut
      (Portkey, design inspiration, streaming, rate limiting) and why.

---

## Definition of done for the whole prototype

Every box above ticked, plus: every claim in the write-ups cites a specific
input, output, file or number. Per the case's own evidence standard,
"retrieval works well" is worth nothing.
