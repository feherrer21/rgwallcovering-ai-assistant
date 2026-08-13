# Corpus Statistics

**Task:** T1.7 (`05_tasks.md`)
**Built:** 2026-08-12
**Command:** `python -m agent_core.ingest.build`

Actual measured counts from the built index, not the counts the sources
advertise. Where the two differ, the difference is recorded below.

## Totals

| | |
|---|---|
| Chunks | **361** |
| Distinct documents | 41 |
| Embedding dimensions | 384 (`BAAI/bge-small-en-v1.5`) |
| Index size on disk | 554,624 bytes (`embeddings.npy`) |
| Chunk length | min 175 / mean 559 / max 820 characters |
| Chunks missing the title prefix | **0** |
| Chunks containing U+FFFD (encoding damage) | **0** |

## By source

| Source | Tier | Chunks | Notes |
|---|:--:|---:|---|
| S0-ronald | A | 4 | Owner's answers, 2026-08-12 |
| S1-home | A | 3 | |
| S1-about | A | 8 | |
| S1-design | A | 7 | Interior Design page |
| S1-contacto | A | 2 | Local doc — see exclusions |
| S1-commercial | A | 14 | |
| S1-residential | A | 13 | |
| S2-blog | A | 273 | 27 posts |
| S4-bbb | B | 4 | BBB + Houzz, third-party |
| S6-duracion | C | 6 | |
| S6-coste | C | 5 | |
| S6-preparacion | C | 5 | |
| S6-visita | C | 5 | |
| S6-residencial-comercial | C | 5 | |
| S6-materiales | C | 7 | |

**Tier distribution:** A 324 (89.8%), B 4 (1.1%), C 33 (9.1%).

That distribution is worth reading carefully. Tier A dominates by volume, but
273 of those 324 chunks — 84% of the whole corpus — are blog essays about
ancient Egypt, block printing and cherry blossoms. The chunks that answer what
customers actually ask are the 4 from Ronald, the 27 from the service and
about pages, and the 33 at tier C. **Roughly 18% of the corpus does the work.**

This is the finding predicted in `02_data_provenance.md` §1.2, now measured
rather than asserted, and it is the empirical case for the relevance floor:
any query lands in a space where 84% of the neighbours are thematically rich
and factually irrelevant.

## Resolved: the 28-vs-27 blog post discrepancy

`02_data_provenance.md` §1.3 recorded that the blog index reports 28 posts
while enumeration returned 27.

**Resolved: 27.** Link discovery on `/blog/` found 29 same-domain URLs. Two of
them are not posts — `/commercial/` and `/residential/`, the service pages —
leaving 27 distinct articles, each ingested exactly once. The 28th advertised
post is not reachable from the index page.

The provenance note's advertised figure of 28 should be read as the site's
claim; 27 is what exists.

## Exclusions applied

| Excluded | Reason |
|---|---|
| `/services/` | Serves WordPress template copy about solar panels, renewable energy and wind turbines. Live on the client's site. A naive crawler would have ingested it. |
| `/portfolio/` | 84 images, no text. Contributes nothing to a text corpus. |
| `/contact/` (as a fetched page) | Every content block sits inside the footer container, which the extractor strips because it repeats on all 35 pages. Lifting the filter for that URL would inject the menu and footer into the corpus 30 times. The contact details are declared once as a local tier-A document with provenance instead. |
| Customer review text | Third-party individuals' words, n=1, not the client's to republish. |

## Notes carried forward

- **The site footer reads "© 2023".** Another staleness signal alongside the
  blog's most recent post being January 2025.
- `/commercial/` and `/residential/` were initially ingested through blog
  discovery and attributed to `S2-blog` — wrong provenance for real service
  pages. They are now declared as their own sources. See
  `ai_review_log.md` entry 4.
