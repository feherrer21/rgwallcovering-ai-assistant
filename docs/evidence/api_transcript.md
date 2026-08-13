# API transcript — every endpoint exercised locally (T4.3)

Recorded 2026-08-13 against `backend.app.main:app` on `uvicorn`, index built
(365 chunks), SMTP configured. Real calls to the model: three.

The server ran with `RATE_LIMIT_POR_MINUTO=3` instead of the default 10 so the
limiter could be shown without spending three more model calls to reach it, and
with `ADMIN_TOKEN=demo-token-local` so `/leads` had something to check against.
Everything else is the shipped default.

Responses are copied verbatim, with one deliberate exception noted at §8.

---

## 1 · `GET /health`

```
$ curl -s http://127.0.0.1:8000/health

{"status":"ok","index_loaded":true,"chunks":365,"email_delivery":true}
[status 200 · 0.018s]
```

Liveness is the easy half. The useful half is `index_loaded`: the process
starts even when the index is missing, so that this endpoint can say so rather
than the container dying with the reason in a log nobody is reading.

## 2 · `POST /chat` — a question the corpus answers

```
$ curl -s -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" \
    -d '{"message": "do you install wallpaper in Newport?"}'

{"reply":"Yes — Newport is well within their area, and for projects in Rhode Island the assessment visit isn't charged.\n\nWhat's the space you're thinking of papering?",
 "sources":[{"title":"What a site visit is for","url":"","tier":"C"},
            {"title":"How RG Wallcovering works — confirmed by the owner","url":"","tier":"A"},
            {"title":"Business details from third-party directories","url":"","tier":"B"},
            {"title":"Interior Design","url":"https://rgwallcovering.com/interior-design/","tier":"A"}],
 "deferred":false,
 "lead":null,
 "conversation_id":"3419266298e3"}
[status 200 · 5.41s]
```

Two things worth noticing. The claim that the visit is not charged rests on a
tier A passage confirmed by the owner, not on the tier C explainer sitting next
to it — the tiers survived ingestion, retrieval and the prompt, which is what
`sources` exists to make checkable from outside the process. And no
`conversation_id` was sent, so the server issued one; the client sends it back
on the next turn.

## 3 · `POST /chat` — history carried, and a question the corpus does not answer

```
$ curl -s -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" \
    -d '{"message": "how much would that cost per room?",
         "history": [{"role":"user","content":"do you install wallpaper in Newport?"},
                     {"role":"assistant","content":"Yes - RG Wallcovering works throughout Rhode Island."}],
         "conversation_id": "demo-transcript"}'

{"reply":"I can't give you a per-room figure — the team quotes after assessing the space, and pricing isn't set by room. What moves it most is the material: a machine-printed paper and a grasscloth or bespoke mural sit in very different brackets, on the same wall.\n\nGood news for Newport: within Rhode Island the assessment visit isn't charged. Want me to pass your details along so they can set one up?",
 "sources":[{"title":"What a site visit is for","url":"","tier":"C"},
            {"title":"2025: A New Beginning for Your Spaces!","url":"https://rgwallcovering.com/2025-a-new-beginning-for-your-spaces","tier":"A"},
            {"title":"How RG Wallcovering works — confirmed by the owner","url":"","tier":"A"},
            {"title":"What drives the cost of a wallcovering project","url":"","tier":"C"},
            {"title":"COMBINE WALLPAPER","url":"https://rgwallcovering.com/combine-wallpaper","tier":"A"}],
 "deferred":false,
 "lead":null,
 "conversation_id":"demo-transcript"}
[status 200 · 7.26s]
```

This is the S2 case, and it behaved: there is no price anywhere in the corpus,
and none was invented. The tier C passage was used the way tier C is supposed
to be used — to explain what *determines* the number without asserting one —
and the turn ended by offering to hand the enquiry over.

The `conversation_id` sent by the client came back unchanged. The server holds
no conversation state; the history travels in the request.

## 4 · `POST /chat` — outside the contract

```
$ curl -s -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" \
    -d '{"message": ""}'

{"detail":[{"type":"string_too_short","loc":["body","message"],
            "msg":"String should have at least 1 character",
            "input":"","ctx":{"min_length":1}}]}
[status 422 · 0.017s]
```

Rejected before it reaches the model. `message` is capped at 2000 characters
and `history` at 40 entries for the same reason: everything accepted here ends
up in a prompt the owner pays for.

## 5 · `POST /chat` — the rate limit

```
$ curl -s -i -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" \
    -d '{"message": "hello again"}'

HTTP/1.1 429 Too Many Requests
retry-after: 48
content-type: application/json

{"detail":"Too many messages in a short time. Please wait a moment — or reach us
 directly at info@rgwallcovering.com / +1 (401) 722-9255."}
```

The fourth request of the minute, against a limit of three. It cost nothing:
the limiter runs as a dependency, so a blocked request never reaches the model.
`Retry-After` carries the real number of seconds — telling someone to wait
without telling them how long is telling them nothing — and the message still
gives a phone number and an address, because a visitor who hits this is a
visitor trying to reach the business.

## 6, 7 · `GET /leads` — without a token, and with the wrong one

```
$ curl -s http://127.0.0.1:8000/leads
{"detail":"Unauthorized"}
[status 401]

$ curl -s http://127.0.0.1:8000/leads -H "X-Admin-Token: nope"
{"detail":"Unauthorized"}
[status 401]
```

Compared with `hmac.compare_digest`, not `!=`.

## 8 · `GET /leads` — with the right token

```
$ curl -s http://127.0.0.1:8000/leads -H "X-Admin-Token: demo-token-local"
[status 200 · 2363 bytes]
```

**The body is deliberately not reproduced here.** It is the one response in
this transcript that contains personal data — three records, with fields
`nombre`, `email`, `ubicacion`, `espacio`, `tipo_proyecto`, `necesita_diseno`,
`resumen`, plus `lead_id`, `conversation_id` and `creado_en`. A file in `docs/`
is a file that gets committed, and lead records do not get committed.

## 9 · `GET /leads` — the shipped default

```
$ ADMIN_TOKEN unset — server restarted without it
$ curl -s http://127.0.0.1:8001/leads -H "X-Admin-Token: demo-token-local"

{"detail":"Not available"}
[status 503]
```

With no `ADMIN_TOKEN` configured the endpoint does not exist for anyone,
correct token or not. That is the default, and it is what a deployment gets
unless someone deliberately turns it on: `03_spec.md` §8 requires this endpoint
to be removed or authenticated before deployment, and an unset variable is the
removal.

---

## What this run establishes

| | |
|---|---|
| Contract of `03_spec.md` §5 | matched field by field, including `sources` and `deferred` |
| Trust tiers survive to the response | §2, a tier A claim next to tier B and C passages |
| No fabricated figure under direct pressure | §3, the price question |
| Statelessness | §3, client-supplied `conversation_id` returned unchanged |
| `/chat` cannot be used as an open invoice | §4 and §5 |
| `/leads` does not serve personal data by default | §9 |

Latency, 5.4 s and 7.3 s, is consistent with the 6–13 s observed in T3.6.

The same paths are covered without spending model calls in `tests/test_api.py`,
which is what runs in CI; this transcript is the evidence that the real process,
over real HTTP, does what the tests assert.
