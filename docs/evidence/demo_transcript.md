# Demo transcript — one conversation that works, one that doesn't

Recorded 2026-08-13 against the shipped configuration: `claude-opus-5`, effort
`low`, relevance floor 0.62, 365-chunk index, deterministic pre-retrieval.
Nothing here is edited. `<sources>` shows what the retriever actually returned
for each turn, with cosine scores.

The visitor is invented. Email delivery was switched off for the recording;
the email below is the real output of `leads.formatear()`, which is what
arrives in the inbox.

---

## Part 1 — What it is supposed to do

A commercial enquiry that starts with a question the website cannot answer and
ends with a lead in Ronald's inbox.

### Turn 1

**Visitor:** Hi — we run a small dental practice in Providence and the reception walls are looking really tired. Do you do commercial work?

**Assistant:** Yes — commercial work is a big part of what they do, including offices and institutional spaces, so a dental reception fits right in.

What are you thinking for the reception — wallcovering, fresh paint, or you're not sure yet?

```
<sources deferred=false 4.5s>
  [B] Business details from third-party directories · 0.685
  [A] Commercial · 0.681
  [A] RG Wallcovering – We turn your walls into works of art · 0.670
  [A] Interior Design · 0.668
  [A] Residential · 0.653
```

### Turn 2 — the S2 gate

**Visitor:** How much would something like that run us?

**Assistant:** I can't put a number on it — every project is priced after the space is assessed, since prep work, wall condition and material choice move the cost far more than square footage does. Since you're in Providence, the assessment visit wouldn't be charged.

Roughly how big is the reception area, and do you have a look in mind already?

```
<sources deferred=false 7.6s>
  [C] What drives the cost of a wallcovering project · 0.782
  [C] What a site visit is for · 0.734
  [A] How RG Wallcovering works — confirmed by the owner · 0.720
```

**This is the whole design in one turn.** There is no price anywhere in the
corpus, and none was invented. The tier C passages explain what *drives* the
cost without asserting a figure; the tier A owner-confirmed document is what
licenses the one concrete claim made — that the visit is not charged nearby.

> **Correction, 2026-08-14.** That claim was false. Ronald corrected the
> underlying fact: the assessment visit is $300 for everyone, distance is
> irrelevant, and it is credited against the installation. This transcript is
> a record of a run that happened and is not rewritten. The point it
> illustrates survives intact — the tiers did their job, the claim was
> licensed by the tier A document rather than invented — but it licensed a
> claim that was wrong, because the tier A document was wrong. Sourcing
> guarantees traceability, not truth.

### Turn 3

**Visitor:** It's the reception area, maybe 30 feet of wall. There's old vinyl wallpaper on it now. We'd want it done before the new year.

**Assistant:** Old vinyl coming off and something new going up is exactly their range — removal is part of what they do. The condition of the walls underneath is usually the thing that decides how much prep is involved, so that's a big part of what the visit is for.

Can I get your name and the best email or phone for you? I'll pass this along so Ronald can get in touch about the visit and the timing before the new year.

```
<sources deferred=false 5.1s>
  [A] 2025: A New Beginning for Your Spaces! · 0.699
  [A] FIVE INTERIOR DESIGN AND WALLPAPER IDEAS · 0.681
  [A] DECORATION DURING THE HOLIDAY SEASON · 0.677
  [A] Residential · 0.673
```

⚠️ **A defect, visible in the demo.** *"Removal is part of what they do"* is
true — the directory listing (tier B) names wallpaper removal as a service.
But **none of the four passages cited on this turn mentions removal**; all
four are decorative blog posts. Checked, not assumed: the three blog documents
contain zero occurrences of "remov" or "strip". So the answer is correct and
unauditable at the same time — failure F4 in `07_failure_analysis.md`,
appearing in the demo rather than only in the evaluation set.

### Turn 4

**Visitor:** That's helpful. Do you do the design side too, or do we need to pick something ourselves?

**Assistant:** Yes — they do the design side. It starts with a consultation about your vision, budget and timeline, then a site visit for measurements and conditions, and you get mood boards, color schemes and layouts to react to before anything gets installed.

So you don't need to arrive with a choice made. Want to send along your name and a phone or email, and I'll get this to Ronald?

```
<sources deferred=false 4.0s>
  [A] Interior Design · 0.706
  [A] OUT-OF-THIS-WORLD DECOR · 0.700
  [A] COMBINE WALLPAPER · 0.684
  [A] INCORPORATE WALLCOVERING IN LARGE-SCALE INTERIOR DESIGN · 0.682
```

Checked: the Interior Design page does say *"Our journey begins with a thorough
consultation where we discuss your vision, needs, budget, and timeline"* and
*"mood boards, color schemes, and preliminary layouts"*. Traceable, word for
word.

### Turn 5

**Visitor:** Great — Elena Vasquez, elena.vasquez@example.com.

**Assistant:** Thanks Elena — your details are with the team now, and Ronald will reach out to set up the assessment visit and talk through options for the reception.

```
<sources deferred=true 10.0s>
  (none — this turn is a handoff, not an answer)
```

### The email Ronald receives

```
Subject: New enquiry — Elena Vasquez (commercial)

Elena runs a small dental practice in Providence and the reception walls are
looking tired. There is old vinyl wallpaper currently on roughly 30 linear
feet of wall that would need to come off before anything new goes up, so wall
condition and prep will be the main unknowns. She has no material or style
picked out and was glad to hear design help is available, so the consultation
and mood board stage will matter to her. She asked about cost and I told her
pricing comes after an assessment, and that the assessment visit would not be
charged since she is in Providence; she also wants the work done before the
new year.

Name: Elena Vasquez
Email: elena.vasquez@example.com
Project type: commercial
Space: Dental practice reception area, roughly 30 linear feet of wall
Location: Providence, RI
Needs design help: yes
Timing: Wants it completed before the new year

Captured: 2026-08-13T18:34:16+00:00
Reference: 2b00f6fbbee6
```

Every clause of that summary corresponds to something the visitor actually
said or the assistant actually told her — including the last sentence, which
records the one commitment made, because Ronald needs to know what she was
already promised before he calls. Five turns, 31 seconds of model time.

---

## Part 2 — A case it handles badly

Required by the brief, and not a hypothetical: this is `Q-02` from the
evaluation set, and it fails in **2 of 7 recorded samples**.

**Visitor:** I manage a dental office and the reception walls look tired.
**Assistant:** *(answers, asks about the design)*

**Visitor:** Commercial, and we'd like it done before the new year.
**Assistant:** *(acknowledges the timing, asks about material)*

**Visitor:** Marcus Webb, 401-555-0142.
**Assistant:** **"Thanks, Marcus. Where's the office located? That's what determines whether the assessment visit is charged."**

The conversation ends there. `registrar_lead` is never called, so **Ronald
never learns that Marcus exists** — despite the assistant holding his name, his
phone number, that it is commercial, the space, and a deadline.

**Why it happens.** Two instructions in the system prompt with no stated
precedence: `<qualification>` wants the project's location, `<saving_the_lead>`
says to register once there is a name and one contact method. Roughly a third
of the time the checklist wins and the assistant asks the outstanding question
instead of banking what it already has. The visitor, having just handed over
their details, has no reason to reply again.

**How we know it is not random noise.** Both failures produced *the same
sentence, word for word*. The shape is deterministic; only whether it fires
varies.

**Status: fixed after this transcript was recorded, and measured.** The
missing sentence was added to `<saving_the_lead>` — register the moment there
is a name and a contact method, then keep asking. Across six samples the
assistant now does both, in that order, in the same message:

> *"Thanks Marcus — **your details are with the team** and they'll reach out to
> set up an assessment. Where is the office located?"*

6 of 6 after, 0 of 7 before. The count alone would not carry it (six clean
runs come up by chance 12.8% of the time at a 29% failure rate) — the change
in shape does. A full 30-question control run afterwards held S2 at zero
violations and captured 5 of 5 leads. `07_failure_analysis.md` §F2.

**The transcript is left as recorded.** The failure was real, it is what the
demo showed, and rewriting it after the fact would erase the only reason
anyone can check the fix. **The live badly-handled case is now turn 3 above** —
correct and unauditable at the same time — together with `A-02` and the
service-boundary answers in §F3 and §F4, all of which remain open with their
reasons.

**Why it is the right failure to show.** It is not a wrong answer or an
invented fact. It is the assistant being *too diligent* about qualifying and
losing the customer while doing it — the failure mode a demo of a happy path
would never reveal, and the one that costs Ronald money.
