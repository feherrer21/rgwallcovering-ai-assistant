# Measured improvement — three experiments, and what the measurement itself taught

Baseline: `baseline_results.md`. S1 80%, S2 0 violations, S3 100%, S4 80%.

Every run below is the same 30 questions through `eval/run.py`, labelled with
`eval/rubric.md`. Raw output for all of them is in `eval/results/`.

**The headline is not any of the three changes. It is that two runs of the
identical configuration differ by as much as any two configurations differ.**
That finding arrived by accident and it reframes everything else on this page.

---

## Experiment 1 — lower the relevance floor, 0.62 → 0.58

`RELEVANCE_FLOOR=0.58`, nothing else touched. Run:
`eval/results/run_20260813_piso0.58.*`

| | Baseline (0.62) | Floor 0.58 |
|---|---|---|
| S1 | 80% (24/30) | **83.3%** (25/30) |
| S2 | 0 violations | 0 violations |
| S3 | 100% (5/5) | 100% (5/5) |

One case moved: `A-01` *"what services do you offer?"*. At 0.58 the tier B
directory listing came in at 0.652, and that listing is the only source in the
corpus for "interior and exterior painting" — so the claim became traceable and
the label went from `unsupported` to `grounded`.

**Decision: keep 0.62.** The gain is one case in thirty, which `02` §2.3
already declared not significant. Against it sits what the sweep
(`eval/sweep.py`) shows waiting just below the floor:

| Question | First passage admitted by lowering | Score |
|---|---|---|
| *"where are you based?"* | "Your favorite place in the world, in your Home" — a decorative blog essay | 0.602 |
| *"do you install hardwood floors?"* | "2025: A New Beginning for Your Spaces!" — marketing prose | 0.597 |

The document that actually holds the address scores **0.559** for that
question — *below* the decorative essay. Lowering the floor does not admit the
right document, it admits the wrong one first. And the flooring case admits
exactly the "we transform spaces" material that phase 2 identified as the thing
most likely to push a generator toward an accidental yes.

That is the S2 argument, and S2 is the criterion with no partial credit. One
label of S1 is not worth widening the aperture on the material most likely to
produce a commitment the business has to honour.

---

## Experiment 2 — tell the model to search even when the prompt answers

The baseline attributed four of the six S1 failures to the service inventory
living in the system prompt. The cheapest counter is to instruct the model that
prompt-answerable facts still require a search.

Added to `<when_to_search>`, floor back at 0.62. Runs:
`run_20260813_busqueda_obligatoria.*` and `..._m2.*`.

| | Baseline | Sample 1 | Sample 2 |
|---|---|---|---|
| S1 | 80% | 80% | 83.3% |
| S2 | 0 | 0 | 0 |
| S3 | 100% | **80%** | 100% |

**Sample 1** fixed `A-06` — the agent searched *"how to contact RG
Wallcovering, phone, email, address"* and cited four passages — and broke
`Q-02`: it spent all three turns asking for the office location and never
registered Marcus at all. A lead that is never captured is not a grounding
problem, it is a lost customer.

**Sample 2**, identical configuration, did not lose that lead. It lost
something else instead: `A-04` *"how long have you been doing this?"* answered
*"I don't have a specific number of years to give you"* — a **false deferral**,
since 2006 is on the company's own About Us page and the baseline answered it
correctly.

Which cases skipped searching entirely:

| | Cases with no search at all |
|---|---|
| Sample 1 | A-02, D-04, D-08, F-03, F-04, Q-02, X-A3, X-A5 |
| Sample 2 | A-01, A-04, D-02, D-08, F-03, F-04, Q-02, X-A3, X-A5 |

Six are stable. Five are not: the same question, the same prompt, a different
decision. **Whether the assistant grounds an answer was a coin flip**, and the
instruction to search did not change that — it changed which questions the coin
was flipped for.

**Decision: reverted.** It buys nothing measurable and it costs a lead in one
sample out of two.

---

## Experiment 3 — stop asking the model to decide: retrieve every turn

If grounding cannot be made reliable by instruction, it should not depend on an
instruction. `run_turn()` now retrieves with the visitor's message *before*
calling the model and hands the passages over in a `<retrieved_passages>`
block. The tool stays — the agent's own queries retrieve better than raw
visitor text, so it refines rather than decides whether to bother.

Floor 0.62, experiment 2's wording reverted. Runs: `run_20260813_previa_m1.*`
and `..._m2.*`.

| | Baseline | Sample 1 | Sample 2 |
|---|---|---|---|
| S1 | 80% | 80% | 83.3% |
| S2 | 0 | 0 | 0 |
| S3 | 100% | 80% | 100% |
| S4 | 80% | 100% | 100% |
| Input tokens | 64,179 | **39,984** | **42,053** |

**The score did not move. Two other things did.**

**Cost fell by a third.** 64,179 input tokens to ~41,000 for the same 30 cases.
Pre-retrieval removes a round trip: without it, a search means sending the
whole conversation again to deliver the tool result. Ronald pays per token, so
a 35% cut is the most concrete thing on this page.

**The failures stopped moving.** This is the point of the change:

| | Cases whose answer was ungrounded |
|---|---|
| Experiment 2, sample 1 | A-02, Q-02, F-03, F-04, X-A5, A-01 |
| Experiment 2, sample 2 | A-01, A-04*, D-02*, F-03, F-04, X-A5, Q-02 |
| **Experiment 3, sample 1** | **A-01, A-02, F-03, F-04, X-A5** + X-A4 |
| **Experiment 3, sample 2** | **A-01, A-02, F-03, F-04, X-A5** |

Five cases fail in both samples, and they are the same five. Before the change,
two runs of one configuration disagreed about five cases. A metric that moves
when nothing changes cannot be improved against; one that holds still can.

And the five that remain have causes, not coin flips:

- **`A-01`, `F-03`, `F-04`, `X-A5`** — the corpus has no document saying what
  the company does and does not do. The answers are right because the service
  inventory is in the system prompt. `X-A5` is the sharpest illustration: it
  now *has* four retrieved passages and is still `unsupported`, because none of
  them says anything about flooring. Retrieved passages do not launder a claim
  they do not support.
- **`A-02`** — *"where are you based?"* retrieves nothing at all, and lowering
  the floor does not help, because the decorative essay at 0.602 outranks the
  document holding the address at 0.559. This is a ranking failure, not a
  threshold failure. It goes to phase 7.

**Decision: keep it.** Not because the score improved — it did not — but
because the same behaviour now costs a third less and stops changing shape
between runs, and because it converts "sometimes ungrounded" into five named
cases with two named causes.

### Two defects the criteria do not see

Found while labelling, recorded because the rubric missing them is not the same
as them not existing:

1. **Lead summaries drift into Spanish.** The conversation is in English, the
   reader works in English, and the summary arrives in Spanish: 1 of 5 at
   baseline, 3 of 4 in sample 1, 2 of 5 in sample 2. S4 scores content, so it
   scores these as passes. The likely cause is the `registrar_lead` tool
   schema, whose field names and enum values are Spanish (`resumen`,
   `necesita_diseno`, `residencial`).
2. **`Q-02` loses its lead in 2 of 5 runs.** The agent keeps asking for the
   office location instead of registering what it already has — a name, a phone
   number, commercial, and the space. S3 counts it as one incomplete case; in
   the business it is a customer who contacted RG Wallcovering and never
   reached Ronald.

---

## What the two negative results establish

The interventions are smaller than the noise. Both configurations produce S1
between 80% and 83.3%, and so does the same configuration run twice. With 30
cases — five of which carry S3 and S4 — the harness cannot resolve a difference
of one or two labels, exactly as `02` §2.3 warned before any of this was built.

So the useful conclusion is not about the floor or the wording. It is about
where the variance lives: **grounding depended on a decision the model made
turn by turn, and that decision was not stable.** No parameter and no sentence
fixes that, because the mechanism is the model choosing whether to look.

Experiment 3 removes the decision rather than trying to influence it, which is
why it is the one that was kept.

---

## Summary

| | Baseline | Floor 0.58 | Search-first | **Pre-retrieval** |
|---|---|---|---|---|
| S1 | 80% | 83.3% | 80% / 83.3% | 80% / 83.3% |
| S2 | 0 | 0 | 0 | **0** |
| S3 | 100% | 100% | 80% / 100% | 80% / 100% |
| Input tokens | 64,179 | 68,801 | 61,020 | **~41,000** |
| Ungrounded cases stable across samples | — | — | no | **yes** |
| Kept | — | no | no | **yes** |

**What got worse:** nothing in the criteria, and two things outside them. The
Spanish drift in lead summaries was worse in sample 1 (3 of 4) than at baseline
(1 of 5), though it appears in every configuration and is more likely to be the
Spanish tool schema than anything measured here. And `Q-02` lost its lead in
sample 1, as it also did in one of the two experiment 2 samples — a failure
that predates all three changes.

**What is still open, with its cause named:** four cases fail because the
corpus never states what the company does and does not do, and one fails
because the embedding model ranks a blog essay above the document holding the
company's own address. Both are corpus problems. Neither is fixed here, and
phase 7 starts from them.
