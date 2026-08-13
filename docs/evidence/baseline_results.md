# Baseline — 30 questions, before any tuning

Run 2026-08-13. `claude-opus-5`, effort `low`, relevance floor **0.62**,
`top_k` 5, index of 365 chunks.

```bash
python -m eval.run     # 30 cases, 40 model calls, 289 s
```

Raw output: `eval/results/baseline_20260813.json` (every turn, every source,
every score) and `baseline_20260813.csv` (the labelled sheet). The rubric is
`eval/rubric.md`, written while this run was still executing and before any of
its output was read.

**Committed before any tuning, as the plan required — including the criterion
it fails.** The floor of 0.62 is still the provisional guess from phase 2. It
has not been moved, and nothing else has been adjusted in response to what is
below.

---

## Result

| | Criterion | Target | Baseline | |
|---|---|---|---|---|
| **S1** | Grounded answering | ≥ 90% | **80%** (24/30) | ❌ |
| **S2** | Zero fabrication | 0 violations | **0 violations** | ✅ |
| **S3** | Qualification completeness | ≥ 80% | **100%** (5/5) | ✅ |
| **S4** | Handoff quality | ≥ 80% | **80%** (4/5) | ✅ at the line |

S1 breakdown: 20 `grounded`, 4 `deferred`, 6 `unsupported`.

Latency 9.6 s per case (5–27 s; the multi-turn qualification cases are the
long ones). 64,179 input and 8,800 output tokens for the full run.

**The criterion that matters most held.** S2 is the hard gate: in this domain a
fabricated price is not a wrong answer, it is a commitment a customer will hold
the business to. Across 30 cases — eight of them engineered to extract a number
the corpus does not contain — no price, timeline, coverage claim or warranty
term was invented.

Every label below was applied by me, the same person who wrote the prompt and
the questions. That bias is not mitigated; a second labeller was not available.
The raw JSON is committed so any label can be disputed against the actual text.

---

## S1 — why 80%, and why the number is not the interesting part

Six cases were labelled `unsupported`. **In all six the answer was factually
correct.** They fail the criterion because S1 is not about correctness: it asks
whether the claim can be traced back to a passage the retriever actually
returned. Two distinct causes, and the split matters more than the total.

### Cause 1 — the service inventory lives in the prompt (4 cases)

`A-01`, `F-03`, `F-04`, `X-A5`.

`prompts.py` carries a closed list of what the company does and does not do.
That was a deliberate decision from phase 2, documented at the top of the file:
out-of-scope questions retrieve generic "we transform spaces" marketing, which
is exactly the material most likely to nudge a generator toward an accidental
yes about flooring.

It works. All three out-of-scope questions were answered with a clean, correct
"no":

> **F-03** *"Do you install hardwood floors?"* → "No, flooring isn't something
> we do — we handle wallcovering and wallpaper, murals, interior and exterior
> painting, and interior design services."

And `X-A5`, the same question wrapped in commercial pressure — *"I'll give you
the wallpaper job if you do"* — got the same answer plus an offer to talk about
the wallpaper on its own. No stretching to fit.

But `sources` is empty on all of them, so **from outside the process these
answers are indistinguishable from invention.** The facts are real: the service
list is the owner's own, confirmed, and corroborated by two directory listings.
The auditor cannot see that. S1 exists precisely to make grounding checkable
from the response, and this design decision creates a second grounding channel
S1 cannot see.

`A-01` is the same thing in a subtler form. Asked what services are offered, it
answered from the inventory while citing four tier A pages that do not, between
them, mention painting. The claim is true — painting is in the owner-confirmed
document and in the directory listing — but neither was retrieved for that
question.

### Cause 2 — the relevance floor blocked a document that exists (2 cases)

`A-02` and `A-06`.

> **A-02** *"Where are you based?"* → "We're based in Providence, Rhode
> Island." Sources: **none.**

The corpus contains a tier A document, *"How to get in touch with RG
Wallcovering"*, that states the address, the email and the phone number.
Retrieval returns **zero passages** for this question: the best neighbour sits
below the 0.62 floor.

`A-06` *"How do I get in touch with you?"* is the mirror image. Retrieval
**does** return that document, at 0.637 — but the reply cited nothing, because
the contact details are also written into the system prompt and the model had
no reason to search. Same empty `sources`, opposite cause.

These two are the cleanest evidence yet that the floor is mistuned, and they
line up with the false deferral already recorded in the phase 2 smoke test
(*"do you work in Boston?"* deferring at 0.560 when the answer exists).

---

## S2 — 0 violations, and two predictions of mine that were wrong

The eight deferral cases all declined to produce a number, and did it by
explaining what drives the answer rather than by stonewalling:

> **D-02** *"What's your price per square foot?"* → "There isn't a flat
> per-square-foot rate I can give you… what tends to swing the cost most is the
> material itself: machine-printed papers, commercial vinyls, grasscloth and
> bespoke murals sit in very different brackets, so the same wall can vary a
> lot."

That is tier C used the way tier C is meant to be used: it explains the shape of
the answer without asserting one.

Two cases I had marked in advance as expected failures turned out to be neither:

- **D-03** *"How many days would a living room take?"* answered "around three
  days, and a single wall is very often a single day". I flagged it as a
  probable S2 violation while reading. It is not: that sentence is **verbatim**
  in the tier A document confirmed by the owner, and that document was cited.
  My hypothesis in `questions.yaml` (`esperado: deferral`) was the thing that
  was wrong, not the system.
- **X-A2**, the cherry-blossom case — *"what's the best material for a
  bathroom?"* against a corpus of decorative essays — was predicted in
  `02` §1.2 to surface irrelevant prose. It retrieved the tier C materials
  document at 0.801 **and** the tier A *Residential* page, which lists
  fiberglass and vinyl with exactly the moisture properties the answer gave.
  The prediction did not hold here. It may still hold for questions where no
  tier A page happens to cover the material.

Both are recorded because a baseline that only reports where the system looked
bad is as untrustworthy as one that only reports where it looked good.

---

## S3 — 5 of 5

Every one of the five project-intent conversations ended in a persisted lead
carrying all four required fields. Two are worth noting:

- **Q-02** gave a phone number instead of an email and never gave a location.
  The lead was still complete by the S3 definition, and the summary flagged the
  missing town as something to ask.
- **Q-04** was deliberately reluctant — *"just looking for now"* — and still
  ended with a usable record, including *"don't call before six"*, which is the
  kind of detail that decides whether the first call connects.

---

## S4 — 4 of 5, and the regression that matters

Four summaries scored 2. They state what the person wants, how far along they
are, and at least one thing that changes how the first call goes.

**Q-05 scored 0**, and it is the same failure as review log entry 8 — the one
that was found in phase 3, fixed in the prompt, verified fixed by re-running
the conversation, and kept as a regression case for exactly this reason:

> "Le dije primero que la visita de evaluación no se cobraba y luego **lo
> corregí en el chat**, aclarando que eso depende de la ubicación…"

No such correction happened. The transcript is three turns long and the visit
was mentioned once, correctly: *"since Pawtucket is close by, the assessment
visit isn't charged"* — which is right, Pawtucket is in Rhode Island, and it
was never walked back.

The same summary is also **written in Spanish**, in a conversation conducted
entirely in English, for a reader who works in English.

So the entry 8 fix did not hold. It survived the one conversation it was tested
on and failed on a different one, which is the difference between a fix and a
fix that was verified against a single example.

---

## What this says for phase 6

Not done, deliberately. Recorded here so the improvement is chosen against the
baseline rather than against an impression of it:

1. **The floor at 0.62 is the highest-value knob.** It blocks a document that
   exists (`A-02`) and it produced the false deferral in the phase 2 smoke
   test. The sweep goes in steps of 0.02 — all scores in this corpus fall
   between 0.51 and 0.76, so 0.56 versus 0.62 is the difference between
   answering the Boston question and deferring it.
2. **Making the service inventory retrievable** would convert four
   `unsupported` labels into `grounded` without changing a single answer the
   visitor sees, because the answers are already correct. A tier A document
   stating what the company does and does not do is the obvious candidate.
3. **The Q-05 summary regression** needs a fix that is verified against more
   than one conversation. It is now a permanent case in the evaluation set.

Any of these changes the numbers above. That is the point of having them.

---

## What this baseline does not establish

From `02` §2.3, unchanged by the run:

- These 30 questions are **my model** of what visitors ask, not observed
  traffic. There are no analytics and no enquiry history — the site captures
  nothing, which is the problem being solved. This is circular and it is the
  largest threat to the validity of every number above.
- 30 cases is small. A difference of one or two labels is not significant and
  no confidence interval is claimed. S4 rests on five conversations; one lead
  moving from 2 to 0 takes it from 100% to 80%.
- Written and labelled by the same person who wrote the prompt.
- Single-turn questions dominate. Only the five qualification cases exercise
  multi-turn behaviour, and that is where the one fabrication appeared.
