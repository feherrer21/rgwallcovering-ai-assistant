# Problem Statement

**Case:** L1_Case05_Open_Choice_Prototype
**Status:** draft — written before any implementation code
**Last updated:** 2026-08-12

---

## Domain

Residential and commercial wallcovering, murals and painting — a small
owner-operated services business. The client is RG Wallcovering & Painting,
Inc. (Providence, Rhode Island), a real business with a real public website
(https://rgwallcovering.com/), trading since 2006 with five employees.

Note the gap between the legal name and the website: the company offers
interior and exterior **painting**, murals, and wallpaper **removal** in
addition to wallcovering installation, but rgwallcovering.com presents almost
exclusively as a wallcovering brand. Painting is therefore in scope for the
assistant — a visitor who asks "do you paint too?" and is told no would be an
actively harmful outcome for the client.

This is a **considered-purchase services** domain, and that shapes everything
below. There is no catalogue and no price list: every job is quoted after
someone understands the space, the material and the wall condition. The unit
of value is not a transaction, it is a qualified conversation.

## Users

There are two, and separating them is load-bearing for the rest of this
document.

**Primary user — Ronald Giraldo, owner and principal of RG Wallcovering &
Painting, Inc.** He is who the system is *for*, and whose time it is meant to
protect. The business has been trading since 2006 and has five employees, so
enquiry handling is not delegated to a sales team — it lands on him. Every
enquiry that arrives without context costs him a call to establish facts that
could have been collected in writing.

**The system's interlocutor — the website visitor.** A homeowner with a room
they want to change, or a facilities/office manager with a commercial space.
Crucially, most of them **do not know what to ask.** They do not know whether
their job is big or small, whether design help is available, or what
information a quote would even require. The system talks to this person; it
serves the owner.

## Problem

The site is a well-presented brochure with no way to start a conversation.
Verified by inspection on 2026-08-12:

- **No contact form on the homepage.** The only conversion paths are a phone
  number and an email address in the footer. The lowest-commitment action
  available to an interested visitor is placing a phone call — a high barrier
  for someone who is still exploring.
- **The Services page serves broken template content.** It currently renders
  placeholder copy about solar panels, renewable energy and wind turbines,
  left over from the original WordPress theme. A visitor who clicks "Services"
  to understand the offering finds text about a different industry.
- **The portfolio carries no information.** 84 images (37 residential, 47
  commercial) with no titles, no descriptions, no styles, no materials, no
  detail pages. A visitor cannot tell what they are looking at.
- **The questions a visitor most wants answered are not answered anywhere on
  the site:** coverage area, whether there is a site visit, how long anything
  takes, and what happens if they have no design yet.

The consequence runs in both directions. The visitor who is not ready to
telephone a stranger leaves with their question unanswered and no trace left
behind. The owner receives the small fraction who do call — arriving cold,
with no scope, no space type and no idea of what they want — and spends the
first ten minutes of every call establishing facts that could have been
collected in writing beforehand.

## Why this is worth solving, in the stakeholder's terms

For the owner, the pitch is not "add a chatbot". It is:

> Every enquiry reaches you already knowing whether it is residential or
> commercial, what the space is, whether they need design help, and how to
> contact them — with a short written summary you read before you dial. And
> the visitors who were never going to phone you leave their details instead
> of leaving.

Two things make this concrete rather than aspirational. First, the marginal
cost of an unqualified call is his own billable time, which is the scarcest
resource in an owner-operated business. Second, the current baseline is not
"a worse chatbot" — it is *nothing*, so any lead captured from a visitor who
would not have telephoned is net new.

## Definition of success

Deliberately narrow and measurable. Each criterion is evaluated against a
fixed evaluation set built for this purpose (see `02_data_provenance.md`),
not against hand-picked demonstrations.

| # | Criterion | Target | How it is measured |
|---|---|---|---|
| S1 | **Grounded answering.** Every answer is either supported by a passage actually retrieved from the corpus, or is an explicit deferral to the team. | ≥ 90% of the 30-question evaluation set | Manual label per answer: `grounded` / `deferred` / `unsupported`. Anything not traceable to a retrieved passage counts as `unsupported`. |
| S2 | **Zero fabrication.** No answer states a price, a timeline, a coverage area, or a warranty term that is not present in the corpus. | **0 violations. Hard gate.** | Targeted adversarial subset of the evaluation set. A single violation fails this criterion outright — no partial credit. |
| S3 | **Qualification completeness.** Conversations carrying real project intent end with a lead record containing name, a contact method, residential/commercial, and a description of the space. | ≥ 80% of scripted project-intent conversations | Inspection of the persisted lead records. |
| S4 | **Handoff quality.** The written summary states what the person wants, how far along they are, and at least one detail that would change how the first call goes. | ≥ 80% of captured leads | Rated against a three-point rubric. Subjective by nature — the rubric and the ratings are published so the judgement can be disagreed with. |
| S5 | **Delivery.** The lead reaches Ronald somewhere he already looks, without him opening a dashboard or the process staying alive. | 100% of captured leads | End-to-end test: capture a lead, confirm it arrives, restart the process, confirm nothing was lost. |

**Amendment, 2026-08-12.** S5 was added after the initial four. The trigger was
a decision to aim for something Ronald can actually use rather than a
demonstration of the idea: without it the prototype writes leads to a local
file that is erased on restart, which means real customer enquiries would be
silently lost. Recorded as an amendment with its reason rather than edited in
silently, because a definition of success that quietly grows to match what was
built is worthless.

**S2 is the criterion that matters most.** In this domain a fabricated price or
timeline is not a wrong answer, it is a commitment the visitor will hold the
business to. A system that defers honestly and often is more valuable than one
that answers confidently and is occasionally wrong.

### What is explicitly *not* claimed as success

- No claim about conversion rate, revenue, or lead volume. There is no
  baseline to measure against — the site currently captures nothing — so any
  such number would be invented.
- No claim that the agent's answers match what the owner *would* have said.
  His actual policies on coverage, site visits and timelines are unknown (see
  the open questions below), and the system is designed to defer on exactly
  those rather than guess.

## Scope

**In scope**

1. Answering visitor questions, grounded in a retrieval pipeline over the
   business's own documents, with honest deferral when the corpus does not
   cover the question. Covers the full service range — wallcovering, murals,
   wallpaper removal, and interior/exterior painting — not just the subset the
   website emphasises.
2. Conversational lead qualification, ending in a persisted structured record
   plus a written summary for the owner.

**Out of scope, and why**

- **Design inspiration with portfolio references.** This was the most
  attractive of the three original ideas and it is being cut deliberately: the
  84 portfolio images carry no titles, styles, materials or descriptions, so
  there is nothing to match a visitor's stated style against. Doing it
  properly requires the owner to tag his own work first. Shipping a version
  that gestures at it would be exactly the "works on three hand-picked inputs"
  failure this case warns about. Recorded as a follow-on, not a feature.
- **Booking / calendar integration.** Requires access to the owner's calendar
  and his scheduling rules. Out of reach for a prototype.
- **Migrating the WordPress site.** Independent of this problem; rejected with
  reasoning in `03_spec.md`.

## Open questions for the client

These are unknown, and the system is built to defer on them rather than
invent answers. Each one answered moves a question from "deferred" to
"grounded" with no code change.

1. ~~Service area~~ — **resolved 2026-08-12 from third-party listings**
   (Houzz, Blue Book): Rhode Island (Providence, Cranston, East Providence,
   Cumberland, Cumberland Hill, Coventry, North Providence, Johnston, Lincoln,
   Greenville, Foster) plus Massachusetts and Connecticut. Needs confirmation
   from Ronald — third-party directory data goes stale.
2. ~~Site visit — free or paid?~~ — **resolved 2026-08-14 by Ronald.** Paid,
   **$300**, the same for everyone regardless of distance; credited against
   the installation if the project goes ahead, and if it does not the client
   keeps the material calculation. Longer assessments — over an hour and a
   half on site — are $500.

   **This one had a wrong answer in the corpus first.** On 2026-08-12 he said
   the charge depended on distance and that nearby visits were free. That was
   ingested as tier A, published, and asserted to visitors for two days before
   he corrected it. Recorded in `02_data_provenance.md` §1.1 (S0), and it is
   the reason S0 is the one source treated as revisable.
3. ~~Time from first contact to written quote~~ — **resolved 2026-08-14:**
   three days where the client already knows which material they want; no
   estimate is issued at all until the material is settled. Installation
   duration was resolved 2026-08-12 (≈3 days for a straightforward job, often
   a single day for one wall).
4. Is wall preparation (removing old covering, repairs) included or quoted
   separately? Note: wallpaper removal *is* listed as a service on Houzz, so
   it is offered — but whether it is bundled or billed separately is unknown.
   Partially covered since 2026-08-12: preparation is always done in-house and
   the warranty rests on it. How it appears on the quote is still open.
5. ~~Can a client supply their own material?~~ — **resolved 2026-08-14:** yes,
   and it is the most common case. The attached conditions are in his contract
   and are not in the corpus.
6. Any warranty on the installation. That there *is* one was confirmed
   2026-08-12. The **term is still open**: on 2026-08-14 he said six months
   and immediately said he had to check the contract because he thought a year
   might be required by law. A figure the source itself flags as unverified
   does not enter the corpus, so the assistant still defers on the length.
7. ~~Should the assistant handle painting enquiries?~~ — **decided
   2026-08-12: yes.** Painting, murals and wallpaper removal are real services
   per BBB and Houzz; excluding them would cost the client work. Ronald should
   still confirm that he wants painting leads through this channel.

## Assumptions to validate

Stated explicitly because they are currently unverified, and the argument
above rests on them:

- That the owner personally handles incoming enquiries. Inferred from the size
  and presentation of the business, not confirmed.
- That enquiry volume is low enough that per-lead quality matters more than
  automation of volume. Inferred from the same.
- That the broken Services page and missing contact form are unintentional
  rather than deliberate choices.
