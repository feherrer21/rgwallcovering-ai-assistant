# Labelling rubric — S1 to S4

**Written while the baseline run was still executing, before any of its output
was read.** `01_problem_statement.md` promised a three-point rubric for S4 and
never wrote it down; writing it after seeing the summaries would have meant
fitting the ruler to the thing being measured.

The labels go in the four blank columns of `eval/results/baseline_*.csv`. One
label per criterion per case, and only where the criterion applies.

---

## S1 — Grounded answering · target ≥ 90%

One of three labels for every one of the 30 cases:

| Label | When |
|---|---|
| `grounded` | Every factual claim about the business traces to a passage in `sources` for that case |
| `deferred` | The answer makes no factual claim about the business and hands off to the team |
| `unsupported` | Anything else — including a claim that is *true* but not traceable to a retrieved passage |

The third row is the one that matters. A correct answer the retriever did not
supply is still `unsupported`: it means the system got lucky, and luck does not
survive a corpus change.

Tier C passages ground an explanation of *what determines* an answer. They
never ground a statement of what this business does. A reply that uses tier C
to say "we do X" is `unsupported`, not `grounded`.

**Pass** = `grounded` or `deferred`.

## S2 — Zero fabrication · target 0 violations, hard gate

Binary, every case: `ok` or `violation`.

A `violation` is any stated price, timeline, coverage area, warranty term, or
availability that is not in the retrieved passages. Hedging does not rescue it:
"typically around $X" is a violation, and so is "usually about a week".

Not violations: explaining which factors drive cost or duration without
attaching a number; repeating a figure that is genuinely in a cited passage.

One violation anywhere fails S2 outright. No partial credit, no averaging.

## S3 — Qualification completeness · target ≥ 80% of the 5 conversations

Applies only to the `calificacion` cases. `complete` requires the persisted
lead record to carry **all four**:

1. a name
2. one contact method — email or phone, either is enough
3. residential or commercial
4. a description of the space concrete enough to picture it

Anything short of four is `incomplete`. A case that never produced a lead
record at all is `incomplete`.

## S4 — Handoff quality · target ≥ 80% of captured leads

Applies to the summary inside each captured lead. Three points:

| Score | Meaning |
|---|---|
| **2** | States what the person wants, how far along they are, and at least one detail that would change how the first call goes. Every clause corresponds to something the visitor actually said |
| **1** | Two of the three, or the third is present but generic — "wants wallpaper" tells Ronald nothing he did not know from the subject line. Still no invention |
| **0** | Misses two of the three, **or contains anything the visitor never said** |

**Any fabrication scores 0 regardless of the rest of the summary.** This is not
symmetrical with the other rows and it is not meant to be: review log entry 8
was a summary that narrated a correction which never happened, and it was
fluent, plausible and would have had Ronald apologising to a customer for a
confusion that never existed. A summary that invents is worse than no summary,
because Ronald cannot tell it apart from a real one.

**Pass** = a score of 2.

---

## How ties and doubt are handled

When a label is arguable, it goes to the worse of the two options and the
reason is written in the results document. The set is 30 cases; one or two
labels moved does not change a conclusion, and a rubric applied generously to
one's own system produces a number nobody can use.
