# AI Output Review — running log

**Task:** T8.1 (`05_tasks.md`)
**Started:** 2026-08-12, at the first implementation task

Errors are recorded here **as they happen**, during the phase that produced
them. Reconstructing them at the end produces the vague, flattering version —
"the AI occasionally made mistakes which I corrected" — which is worth
nothing. The write-up across intent / tests / security / performance /
maintainability is phase 8; this file is the raw material.

---

## Phase 1 — Ingestion

### Entry 1 — Crash: iterating a tree while mutating it

**Dimension:** correctness
**Severity:** low (loud failure, immediate)

```
AttributeError: 'NoneType' object has no attribute 'get'
  extract.py:24 in _es_ruido
```

The generated `extraer()` collected `sopa.find_all(True)` and called
`.decompose()` on matching tags while still iterating that list. Decomposing a
parent invalidates its descendants, which remain in the already-materialised
list with `attrs` set to `None`.

**Fix:** freeze the list with `list(...)` before mutating, and make
`_es_ruido` return `False` for a tag whose `attrs` is falsy.

This is the easy category of error: it announces itself.

---

### Entry 2 — The one that mattered: a filter that silently emptied the corpus

**Dimension:** correctness
**Severity:** high (silent, and would have poisoned everything downstream)

The first successful build reported **41 chunks and exited 0**. Every local
document was present. Every web source returned **zero**, and nothing in the
output said so — the per-source table showed `0` next to five sources and the
run looked like a success.

Cause: the noise filter matched class and id attributes by substring against
`("menu", "nav", "sidebar", "footer", "header", "cookie", ..., "widget")`.
rgwallcovering.com is built with Elementor, which wraps **every** content
element in classes containing `widget` — `elementor-widget`,
`elementor-widget-container`. The filter therefore decomposed the entire page
on every page.

Diagnosis: instrument the extractor and count blocks before and after
filtering.

```
=== https://rgwallcovering.com/
  bloques: 53 | con >=25 chars: 16
  bloques bajo un ancestro marcado como ruido: 53      <-- 53 of 53
  texto extraido: 0 chars
```

**Fix:** replace the generic needles with the containers Elementor actually
uses for template chrome — `elementor-location-header`,
`elementor-location-footer` — plus specific names like `nav-menu`,
`menu-item`, `breadcrumb`. Result: 41 → 361 chunks.

**Why this is the entry worth reading.** The failure mode was not a wrong
answer, it was an *absence* reported as a success. Had it gone unnoticed, the
assistant would have been grounded on 41 chunks of local knowledge with none
of the client's own content, and it would still have produced fluent,
confident answers — the retrieval would simply have had nothing real to
retrieve. Nothing in the pipeline would have complained.

**Process lesson, not a code fix:** a build that produces zero output from a
source should be an error, not a row in a table. Not yet implemented; recorded
as a real gap.

---

### Entry 3 — Encoding assumed rather than forced

**Dimension:** correctness
**Severity:** medium (silent, reached the corpus)

Page titles arrived as `RG Wallcovering � We turn your walls into works of
art`. `requests` falls back to ISO-8859-1 when a response declares no charset;
the site is UTF-8. The damaged characters were written into the first index.

Secondary effect: the regex that strips the site name from `<title>` failed to
match, because the separator it was looking for had been corrupted.

**Fix:** set `respuesta.encoding = respuesta.apparent_encoding` when the
declared encoding is absent or the ISO-8859-1 default.

**Verified rather than assumed:** counted U+FFFD occurrences across all 361
chunks after the rebuild — zero. The `�` still visible in terminal output is
the Windows console codepage, not the data. Worth separating, because the two
look identical and one of them is harmless.

---

### Entry 4 — Correct content, wrong provenance

**Dimension:** correctness / data integrity
**Severity:** medium

Blog link discovery returned 29 URLs. Two — `/commercial/` and
`/residential/` — are service pages, not posts, and were ingested with
`source_id: "S2-blog"`.

The text was real and useful, so nothing looked broken. But in a system whose
central safety mechanism is that every claim is traceable to a source, content
filed under the wrong source is a defect regardless of whether the text is
good.

**Fix:** declare both as their own sources and exclude them from discovery.
This also resolved the 28-vs-27 discrepancy recorded in the provenance note —
see `corpus_stats.md`.

---

### Entry 5 — A catch that was applied before it broke anything

**Dimension:** correctness
**Severity:** would have been high

During the context-artifact experiment, the generating subagent flagged
unprompted that it had used fastembed's `query_embed()` — which applies the
BGE query-instruction prefix — and that this is correct only if ingestion
embeds passages with plain `embed()`.

BGE is an asymmetric model. Getting this backwards degrades every similarity
score in the system by a small amount, uniformly, with no error and no
symptom other than retrieval that is quietly worse than it should be.

Applied preventively in `build.py`, with a comment explaining why, before any
index was built.

Recorded because it is a case of the model catching something rather than
causing it, and both directions belong in an honest review.

---

## Phase 2 — Retrieval

### Entry 6 — Smoke test on the real corpus: the predicted failure, observed

**Dimension:** correctness / product behaviour
**Severity:** open — deliberately not fixed yet

Eight queries against the built index at the provisional floor of 0.62.
Recorded here rather than acted on: calibrating the floor is phase 6, against
the full evaluation set. Tuning it now, against eight queries chosen by the
person who wrote the code, is how a prototype ends up fitted to its own demo.

**Working as intended:**

| Query | Result |
|---|---|
| *"how long does an installation take?"* | Ronald's answers (A, 0.685) + trade knowledge (C, 0.648) |
| *"do you remove old wallpaper?"* | Preparation doc (C, 0.759) |
| *"what is the capital of Mongolia?"* | **Defers.** Best neighbour 0.512, below floor |

**Failure 1 — false deferral.** *"do you work in Boston?"* defers at 0.560,
but the answer exists: Ronald confirmed Rhode Island and Massachusetts, and
Boston is in Massachusetts. The floor is too high for this query. The
assistant will say "let me have the team confirm" to a question it can
actually answer, which is a real product cost even though it is the safe
direction to fail in.

**Failure 2 — the cherry-blossom effect, measured.** *"what's the best
material for a bathroom?"* returns the materials document (C, 0.666) — and
then, essentially tied with it:

```
[A] 0.658  OUT-OF-THIS-WORLD DECOR
[A] 0.658  Residential
[A] 0.643  FIVE INTERIOR DESIGN AND WALLPAPER IDEAS
[A] 0.638  2025: A New Beginning for Your Spaces!
```

Decorative essays scoring within 0.03 of the one document that genuinely
answers the question. This is the prediction from `02_data_provenance.md`
§1.2, now observed rather than argued: in a corpus that is 84% decorative
prose, the signal and the noise occupy the same score band.

**Failure 3 — out-of-scope queries do not defer.** *"can you install flooring
for me?"* returns generic marketing chunks at 0.62. Nothing in the corpus says
they do not do flooring, so the nearest neighbours are "we transform spaces"
boilerplate — which is exactly the material most likely to lead a generator
toward an accidental yes. Handling this may belong in the prompt rather than
the retriever.

**Structural observation:** all scores across all eight queries fall between
0.51 and 0.76. `bge-small` compresses cosine similarity into a narrow band, so
the floor is a sensitive knob: 0.56 versus 0.62 is the difference between
answering the Boston question and deferring it. Phase 6 should sweep in steps
of about 0.02, not 0.1.

**Also noted:** *"2025: A New Beginning for Your Spaces!"* surfaces across
unrelated queries. It appears to be generic marketing prose that sits near the
centroid of the corpus — a hub chunk that is close to everything and specific
to nothing.

---

## Phase 3 — Agent

### Entry 7 — Two suspected fabrications, both wrong. Mine, not the model's.

**Dimension:** correctness of the *review process*
**Severity:** would have been high — a false finding in a report is worse than
no finding

The first end-to-end conversation produced two claims I flagged as
fabrications on sight:

1. *"Paula on our team does full interior design"* — a named employee, in a
   corpus whose only named person is Ronald Giraldo.
2. *"dry-erase wallcovering for conference rooms… works as a writable surface
   instead of a whiteboard"* — a specific product claim, oddly detailed.

**Both are grounded in tier A.** Paula is the interior designer, described at
length on the company's own Interior Design page — a Suffolk University
graduate, with her design philosophy set out in the first person. The
dry-erase product occupies several paragraphs of the Commercial page,
including its resistance to ghosting.

Checked with a grep before writing either of them down, which is the only
reason this is an entry about my judgement rather than a false finding in the
failure analysis.

**The lesson is about calibration, not about the model.** Fluent, specific,
confident output *reads* like fabrication when you are looking for
fabrication. Suspicion is not evidence in either direction; two greps settled
both in under a minute. Every claim in the failure analysis gets the same
treatment, and any that cannot be checked gets labelled as unverified rather
than asserted.

---

### Entry 8 — The real one: a fabricated correction in the handoff summary

**Dimension:** correctness
**Severity:** high — in the single field the whole product exists to produce

The lead summary written for Ronald contained:

> "Note: I first told her the assessment visit would be free because she's
> nearby, then corrected myself and said the team confirms whether there's a
> charge depending on travel — worth clearing that up early in the call."

**No such exchange happened.** The visitor asked whether the visit is charged
and received one clean sentence: *"Pawtucket's right nearby, so no charge for
the assessment visit."* There was no correction, no walk-back, nothing to
clear up.

The most likely cause is that the model weighed both answers internally —
Ronald's confirmed rule says nearby visits are not charged, while the tier C
material says practice varies — settled on the right one, and then narrated
the deliberation as though it had been an exchange with the visitor.

**Why this is the worst kind of error for this product.** The summary is not a
convenience; it is the deliverable. Ronald reads it and picks up the phone.
Acting on this one, he would have opened the call apologising for a confusion
that never existed, in front of a customer who was never confused — damaging
his own credibility using a tool that was supposed to protect it. And it would
have been invisible: the summary is plausible, well written, and the only
person who could catch it is the visitor, who never sees it.

**Fix:** the prompt now states that the summary records only what the visitor
actually saw, that weighing an answer and settling on it is not a correction
and does not belong in the summary at all, and *why* — that an invented
correction is worse than telling Ronald nothing.

**Verified by re-running the same five-turn conversation.** The new summary:

> "I told her the assessment visit isn't charged since Pawtucket is nearby,
> and gave her only a rough sense of timing… so pricing and dates are still
> open."

Every clause corresponds to something actually said. Kept as a permanent
regression case for phase 5's evaluation set.

**Also fixed:** the tool schema's enum values are Spanish (`comercial`), and
they were reaching Ronald's English-language email verbatim. Translated at
formatting time.

---

## Phase 4 — Frontends

### Entry 9 — The demo served HTTP 200 while being completely broken

**Dimension:** correctness / verification method
**Severity:** medium — it would have failed in front of Ronald, not in a test

The generated `demo_streamlit/app.py` began with `from agent_core import ...`.
The smoke test was a request to the app's root URL; it returned 200 and the
startup log was clean, so the demo looked verified.

It was not. `streamlit run` inserts the *script's* directory into `sys.path`,
not the repository root, and Streamlit does not execute the script until a
browser session connects over its websocket. So the 200 came from a server
that had never run a line of the app. The first person to open the page — the
owner, in the intended case — would have got a `ModuleNotFoundError` traceback
rendered in the browser.

Running the script directly, `python demo_streamlit/app.py`, surfaced it in one
command:

```
ModuleNotFoundError: No module named 'agent_core'
```

**Fix:** the demo prepends the repository root to `sys.path` itself, so it
works whichever way it is launched rather than only from one working directory.

**Why it is in this log.** The bug is unremarkable; the near-miss is not. The
evidence that satisfied me — a 200 and a clean log — was evidence about the web
server, not about the application. That is the same mistake as entry 2, where
the ingestion build reported success over an empty corpus: an artefact that
reports health while the thing it wraps is broken.

---

### Entry 10 — The same blind spot as entry 9, one commit later

**Dimension:** correctness / verification method
**Severity:** medium — the deployed app crashed on open, for everyone

The password gate was factored into one function and called from two tabs. It
creates its widget with a fixed `key="clave"`, and Streamlit refuses two
widgets with the same key in one pass, so the app raised
`StreamlitDuplicateElementKey` at startup on Community Cloud. Every visitor got
an error page instead of an assistant.

Both checks I had run passed. `python demo_streamlit/app.py` executes the
script with no session, so no widget registry exists to collide in. Requesting
the served page returns 200 without executing the script at all — exactly the
gap entry 9 was written about. I had recorded the lesson and then reused the
same method.

**Fix:** the key is now derived per section, `clave_leads` and
`clave_recipients`; the unlocked state stays shared, so one password still
opens both.

**What actually closes it:** `streamlit.testing.v1.AppTest` runs the script
with a real session context, in-process, without a browser. Three tests in
`tests/test_demo.py` now assert the app starts clean with both protected tabs
present, that the right password opens them, and that the wrong one does not.
The first of those fails against the previous commit.

**The lesson, restated because writing it down was not enough:** a verification
that cannot reach the layer where the bug lives is not weak evidence, it is no
evidence. The question to ask of a check is not "did it pass" but "what class
of failure could this have seen".

---

## Phase 5 — Baseline

### Entry 11 — The entry 8 fix did not hold

**Dimension:** correctness / regression
**Severity:** high — it is the failure mode this project treats as worst

Entry 8: a lead summary narrated a self-correction that never happened. The
prompt was changed, the same five-turn conversation was re-run, the summary
came back clean, and the case was kept as a regression case for the evaluation
set. That was the right instinct and an insufficient test.

In the baseline run, `Q-05` — a different conversation, three turns, a visitor
who wants design help — produced:

> "Le dije primero que la visita de evaluación no se cobraba y luego **lo
> corregí en el chat**, aclarando que eso depende de la ubicación…"

Nothing was corrected. The visit was mentioned once, correctly, and never
walked back. The summary is also in Spanish, in an English conversation, for a
reader who works in English.

**Why it recurred:** the fix was verified against the single conversation that
exposed it. One example is enough to show a bug is present and never enough to
show it is gone. The evaluation set is what makes the difference — this was
caught by a run that exercises five different qualification conversations,
which is the first time the fix met a case it had not been tuned against.

**Not fixed yet, on purpose.** The baseline is committed before any tuning,
including this. The fix and its measurement belong to phase 6, and this time
the verification is five conversations, not one.

---

## Phase 6 — Measured improvement

### Entry 12 — My sweep measured an input the system never receives

**Dimension:** correctness of the *measurement*
**Severity:** would have been high — it would have justified a parameter change
with evidence about something else

The first version of `eval/sweep.py` swept the relevance floor by retrieving
with each question's raw visitor text. Its output contradicted the baseline
immediately: it claimed `A-04` retrieves nothing above 0.56, when that case had
retrieved six passages in the real run with a top score of 0.791.

The contradiction was the sweep's, not the run's. **The agent does not search
with the visitor's words.** It calls `buscar_informacion` with a query it
formulates itself, and that query retrieves considerably better than the raw
question. Sweeping raw text measures a distribution the retriever never sees.

Caught only because the two numbers sat next to each other and disagreed. A
sweep run before the baseline would have looked perfectly reasonable, and the
floor would have been chosen against it.

**Fix:** `run.py` now records the agent's actual query strings per turn, so the
real distribution is recoverable from any run. `sweep.py` keeps the raw-text
sweep, relabelled as what it is — a worst case, useful for seeing which
documents sit just below the floor, not for predicting a run.

---

## Phase 7 — Failure analysis

### Entry 13 — The instruction was in two places, and the weaker-looking one won

**Dimension:** correctness / instruction design
**Severity:** medium — 45% of the product's actual deliverable was affected

Lead summaries arrived in Spanish for English conversations — 15 of 33 across
seven samples. The cause was not drift. It was an instruction: the `resumen`
field of the `registrar_lead` schema said *"In the conversation's language."*

Two things came out of fixing it.

**First, the instruction existed twice** — in the tool schema and in
`<saving_the_lead>` in the system prompt, worded differently, saying the same
wrong thing. Finding one and declaring the cause found would have produced a
fix that didn't work, and a confident write-up explaining why it should have.

**Second, and more useful: only the schema was changed, and the result went to
15 of 15 English while the system prompt still said the opposite.** The
field-level description beat the system prompt outright. That is worth
remembering the next time an instruction in the prompt appears to be ignored:
check whether a tool schema is quietly contradicting it.

The prompt line was then corrected too, for coherence — but after the
measurement, and it is recorded here as the cleanup it was rather than as part
of the fix.

---

### Entry 14 — Six clean samples are not a fix; the change in shape is

**Dimension:** correctness of the *claim*, not of the code
**Severity:** low as a defect, high as a habit

`Q-02` lost its lead in 2 of 7 samples. A precedence sentence was added to
`<saving_the_lead>` and the next six samples came back clean — 6 of 6.

The tempting write-up is "fixed: 6/6". It would be wrong. With a 29% failure
rate, **six clean runs come up by chance 12.8% of the time** — better than a
coin flip's worth of evidence, and nowhere near proof. This is the exact
mistake entry 11 recorded: a phase 3 fix verified against the single
conversation that exposed it, which then failed on a different one.

What makes the claim defensible is not the count but the **change in shape**.
Before, the assistant chose between banking the lead and asking the
outstanding question, and sometimes chose wrong:

> *"Thanks, Marcus. Where's the office located?"*

After, it stops choosing:

> *"Thanks Marcus — your details are with the team… Where is the office
> located?"*

That behaviour appears in 6 of 6 runs after and in 0 of 7 before. It is direct
evidence that the added rule is what is acting, rather than that three coins
landed the same way — and it is the kind of evidence a pass/fail count cannot
produce on its own.

**The habit worth keeping:** when a fix is probabilistic, look for a
mechanism you can see in the output, not just a rate you can count.

---

## Running observations

- **Three of the five entries were silent failures.** The one that crashed was
  by far the cheapest to fix. The expensive ones all reported success.
- Generated code defaults to defensive breadth — matching many possible class
  names, tolerating many possible schemas — which reads as robustness and in
  practice was the direct cause of entries 2 and 4.
- **A green signal from the wrapper is not a green signal from the thing
  wrapped.** Entry 2's build reported success over an empty corpus; entry 9's
  web server reported 200 over an application that had never run. Both times
  the check was one layer above where the failure was.
- The pattern that caught entries 2, 3 and 4 was the same each time: **measure
  the output rather than read the code**. Counting blocks before and after a
  filter, counting U+FFFD, listing discovered URLs. None of these bugs were
  visible by inspection; all three were obvious within one command of
  instrumenting.
