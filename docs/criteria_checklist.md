# Submission Checklist — L1_Case05_Open_Choice_Prototype

You chose this case, so you own the scope. Everything below is required
regardless of what you built.

## Define

- [ ] Problem statement: the domain, the user, the problem, and your definition of success.
- [ ] Why this problem is worth solving, in terms a client stakeholder would recognise.
- [ ] Data provenance note: where the data came from or how you generated it, what it does and does not represent, its known limitations, and how you handled anything sensitive.

## Build

- [ ] Working prototype, demonstrable end to end. Polish is explicitly not scored.
- [ ] Spec, plan, and task artifacts, with commit history showing they preceded the implementation.
- [ ] A context artifact (`CLAUDE.md` or `.github/copilot-instructions.md`) plus before-and-after evidence of its effect on output quality.
- [ ] Either a retrieval pipeline over your own documents or a working AI-in-the-loop n8n automation, with a stated reason for choosing that over the other.

## Prove

- [ ] Your review of what the AI generated for you, across intent, tests, security, performance, and maintainability — including at least one error you caught and corrected.
- [ ] Failure analysis naming specific inputs that break the prototype and why.
- [ ] One measured improvement: the before state, the change, the after state, and anything that got worse.

## Communicate

- [ ] One slide pitching the solution to client stakeholders.
- [ ] A short demo (recording or transcript), including at least one case it handles badly.
- [ ] Declared-effort statement: approximate hours and what you cut.

## Evidence standard

Every claim cites a specific input, output, file, or measured number. "Retrieval
works well" scores nothing. "On these three queries the assistant cited the wrong
source document, because my chunking split the table away from its heading"
scores.

## Before you submit — challenge your own work

- [ ] Is the problem I chose narrow enough that I have actually solved it, rather than gestured at it?
- [ ] Can I explain every significant decision and the alternatives I rejected?
- [ ] Would my solution survive being pointed at data I did not choose?
- [ ] Have I named specific inputs where it fails, or only described failure in general terms?
- [ ] Does my write-up let the work speak for itself, without guessing at how it will be scored?

## How this will be assessed

There is no answer key for this case, because you defined the problem. You are
scored against the criteria for your level and against your own stated definition
of success — so a vague definition of success is not a safe choice, it is an
unscoreable one.

Two things carry disproportionate weight:

1. **Your data.** Where it came from, what it does and does not represent, and
   whether it contains cases that genuinely stress your solution. Data selected
   to flatter the prototype is a finding against you, not a neutral choice.
2. **Your failure analysis.** Specific inputs, specific wrong outputs, specific
   causes. "It sometimes struggles with ambiguous cases" is not a failure
   analysis.

You will answer several questions about your own submission at submission time.
They are generated from what you submitted — your stated problem, your data
decisions, your architecture — so they cannot be prepared in advance.
