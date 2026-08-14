# Client Question Script — Ronald Giraldo

Working artifact, not an assessment deliverable. Its purpose is to close the
information gaps the assistant currently has to defer on but could answer.

## How to use it

**Do not send this as a form.** A contractor with five employees and jobs in
progress does not fill in a six-point questionnaire by email — it either gets
postponed indefinitely or answered in two lines.

What works is a fifteen-minute call with you taking the notes. The questions
below are phrased the way they would actually be said out loud, not the way
they would be written on a form. If it has to be in writing, send **three at
most** — the first three.

Ronald can answer in English or Spanish; the corpus is normalised at
ingestion and the assistant replies in the visitor's language either way.

Open with what matters to him, not with what is missing from the corpus:
*"I want the assistant to answer the way you would, and there are five things
I can't know without asking you."*

---

## Status, 2026-08-14

He answered five. Where each one landed:

| | Question | Status |
|---|---|---|
| 1 | Site visit | ✅ **$300**, same for everyone, credited to the installation; $500 for assessments over 90 minutes on site |
| 2 | Timelines | ✅ Quote in **3 days** if the material is decided; **no quote at all** until it is |
| 3 | Wall preparation | ⬜ Not answered — how it appears on the quote is still open |
| 4 | Customer-supplied material | ✅ Yes, and it is the common case. Conditions are in his contract |
| 5 | Warranty | 🟡 Said six months, then said he had to check the contract. **Not usable** — see below |
| 6 | Service area | ⬜ Not answered |
| 7 | Is the service list complete | ⬜ Not answered — still blocks `F-03`, `F-04`, `X-A5` |

**The visit answer reversed a fact that was already published.** On 12 August
he said the charge depended on distance and nearby visits were free. That went
into the corpus as tier A and the assistant asserted it to visitors for two
days. Asking the question a second time, in different words, is what caught
it. Worth remembering when planning the handover: the only control that
catches a wrong tier A fact is Ronald reading back what the assistant says.

**The warranty answer is why "he said it" is not the same as "it is
confirmed."** He gave a number and in the same breath said he had to check the
contract and thought the law might say otherwise. A source flagging its own
answer as unverified is not a source. It stays deferred until the contract
arrives.

### Still to ask him

Four follow-ups from the answers themselves, plus what was never answered:

- **The contract** — settles the warranty term and the customer-material
  clause. He offered to send it.
- **Between one hour and an hour and a half** — is that $300 or $500? He gave
  a rule for "up to an hour" and a rule for "more than an hour and a half".
- **Are the $500 also credited** against the installation, like the $300?
- **When is the fee paid** — at booking, or on the day?
- Questions **3, 6 and 7** above, and the two operational ones below.

---

## The questions, ordered by value

### 1. The site visit

> *"When somebody contacts you about a project, do you go and look at the
> space before quoting? Is that something you charge for, or is it included?"*

**Why this is first.** It is what every visitor wants to know and does not
ask: *what happens after I hand over my details?* Right now the assistant has
to say "the team confirms that directly", which is exactly the point where
people abandon. If the answer is "yes, and it's free", that is a selling point
that currently appears nowhere on his website.

### 2. Timelines

> *"From someone first getting in touch to you sending a quote, how long does
> that usually take? And a normal installation — one room, say — how many days
> is that?"*

**What it unlocks.** The second most common question. Ask for ranges, not
commitments — *"two to five days"* is perfectly usable and commits him to
nothing. If he would rather not give timelines at all, that is also a valid
answer: the assistant keeps explaining what makes a job longer or shorter,
without a figure.

### 3. Wall preparation

> *"If a wall comes with old paper on it, or it's in bad shape, is that part
> of the job or does it go separately on the quote?"*

**Why it matters.** This is the classic mid-job surprise that sours a
customer. Knowing it up front prevents the misunderstanding, and since he
offers wallpaper removal as its own service there is something concrete to
say.

### 4. Customer-supplied material

> *"If somebody already bought their own wallpaper, do you still install it?
> Or would you rather supply it yourself?"*

**What it unlocks.** A very common enquiry from people who bought at a store
and then got stuck. Right now the assistant cannot tell whether that is a
customer or a no.

### 5. Warranty

> *"Do you give any kind of guarantee on the installation?"*

Short question. If there is one it is a strong argument; if there is not, the
assistant should not imply otherwise.

### 6. Confirm the service area

> *"The Houzz listing says you cover Rhode Island, Massachusetts and
> Connecticut — is that still right? Anywhere you don't go any more?"*

**This one is confirmation, not discovery.** We already have it from
third-party directories, but that data ages without warning and the assistant
would be asserting something Ronald has never seen. If he confirms it, it
moves from tier B to tier A.

### 7. Is the service list complete?

> *"So the work is wallcovering, wallpaper removal, murals, painting and the
> design side. Is that the whole list — is there anything else you take on, and
> anything people ask for that you always turn down?"*

**Added 2026-08-13, from the phase 7 failure analysis.** The assistant already
tells visitors "no, flooring isn't something we do", and it is right — but
that "no" rests on an inference from what he told us he *does*, not on
anything he has confirmed. Until he answers, the negative cannot be written
into the corpus as a tier A fact without breaking the zero-fabrication rule,
which is why `F-03`, `F-04` and `X-A5` stay unauditable in
`07_failure_analysis.md` §F4.

The second half of the question is the valuable half: the things people ask
for and never get are exactly the enquiries worth deflecting before they cost
him a call.

---

## Two operational things needed from him

- **Which address should leads go to?** Assuming `info@rgwallcovering.com`.
  If he prefers another, or his mobile, it is a one-line change.
- **Does he want painting enquiries through this channel?** The business is
  "Wallcovering **& Painting**" and offers interior and exterior painting, but
  his website barely mentions it. We decided to include it; he should know
  that and confirm.

---

## Two things to tell him, not ask him

### The Services page is broken, and it is live

`rgwallcovering.com/services/` currently serves template copy about **solar
panels, renewable energy and wind turbines** — leftovers from the original
WordPress theme. Anyone clicking through to see what he does finds that.

This is independent of the project and is probably worth more than half the
prototype. Tell him early.

### Tagging the portfolio would give a capability back

His 84 photos have no titles, styles or descriptions. That is why the
capability where the assistant recommends references matching a visitor's
described style was cut — there is nothing to match against.

If he tags **15 or 20** of his favourites — room, style in two or three words,
material if he remembers it — that capability becomes viable. It is half an
hour of his time, and it is the only item on this list that cannot be done
without him.

---

## What happens to the answers

Each answer enters the corpus as **tier A** and stops being a deferral. No
code changes: the assistant starts answering that question as soon as the
fact exists.

If some go unanswered, nothing breaks — the system is designed for exactly
that. But each one obtained is a conversation that ends in an answer rather
than in "leave me your details".
