# Wiki Schema

> Operational rules for HermesKM. Purpose and boundaries are defined in `purpose.md` — this file derives from it.

## Domain
RPA engineering + AI integration knowledge base covering:
- Research & Horizon (AI Agent architecture, MCP, Agentic RPA)
- Personal Synthesis (career, methodology, system design)
- Technical Knowledge Base (tools, languages, automation engines)
- Scenario Solutions (reusable architecture patterns)
- RPA Production & Delivery (stability, scheduling, audit, security)

## Language Policy
All wiki pages (`wiki/`, `000_Inbox/` processed content) **must be in Chinese**.
Raw source material (`raw/`) retains its original language.

## Conventions
- File names: lowercase, hyphens, no spaces (e.g., `shadow-dom-scraping.md`)
- Every wiki page starts with YAML frontmatter (see below)
- Use `[[wikilinks]]` to link between pages (minimum 2 outbound links per page)
- When updating a page, always bump the `updated` date
- Every new page must be added to `index.md` under the correct section
- Every action must be appended to `log.md`
- **Provenance markers:** On pages that synthesize 3+ sources, append `^[raw/articles/source-file.md]`
  at the end of paragraphs whose claims come from a specific source. This lets a reader trace each
  claim back without re-reading the whole raw file. Optional on single-source pages where the
  `sources:` frontmatter is enough.
- **All content in Chinese** — per purpose.md Language Policy.

## Inbox-to-Wiki Pipeline

> Multi-agent capture and review rules are defined in `docs/agent-knowledge-protocol.md`.
> This schema keeps the page format rules; the protocol controls roles, permissions, and review state.

```
User input → 000_Inbox/ (implicit-capture) → review + dedup → wiki/concepts|entities|comparisons|queries/
```
- All auto-captured pages land in `000_Inbox/` with tag `implicit-capture`
- After review and de-duplication against existing wiki pages, graduate to `wiki/`
- Orphan inbox pages are surfaced in lint reports

## Frontmatter
  ```yaml
  ---
  title: Page Title
  created: YYYY-MM-DD
  updated: YYYY-MM-DD
  status: active | draft | archived
  type: entity | concept | comparison | query | summary | note | guide
  tags: [from taxonomy below]
  # Implicit captures MUST include:
  # tags: [implicit-capture, ...other-tags]
  source_refs: [raw/articles/source-name.md]
  origin_candidate: 000_Inbox/source-candidate.md
  # Legacy pages may still contain sources: [...]
  # Optional quality signals:
  confidence: high | medium | low        # how well-supported the claims are
  contested: true                        # set when the page has unresolved contradictions
  contradictions: [other-page-slug]      # pages this one conflicts with
  ---
  ```

### raw/ Frontmatter

Raw sources ALSO get a small frontmatter block so re-ingests can detect drift:

```yaml
---
source_url: https://example.com/article   # original URL, if applicable
ingested: YYYY-MM-DD
sha256: <hex digest of the raw content below the frontmatter>
---
```

The `sha256:` lets a future re-ingest of the same URL skip processing when content is unchanged,
and flag drift when it has changed. Compute over the body only (everything after the closing
`---`), not the frontmatter itself.

## Tag Taxonomy

### Domain (purpose.md §1)
- rpa, automation, workflow, bot, agent, ai-agent, mcp
- research, exploration, trend-analysis
- personal, career, methodology, system-design

### RPA & Automation
- rpa-tools: uipath, yindao, aa, blueprism
- automation-engines: selenium, playwright, puppeteer, ocr
- scenarios: data-entry, invoice-processing, sap-automation, web-scraping, email-automation, excel-automation, approval-flow
- production: unattended, scheduling, logging, credential-mgmt, queue

### Technical Stack
- languages: python, javascript, sql
- infrastructure: docker, linux, windows, wsl, api, auth, database, cloud
- browser automation: browser-automation, chrome, cdp, web-scraping
- vendors/products: lingxing

### Capture & Knowledge
- implicit-capture       # MUST tag for all 000_Inbox/ entries
- entity, concept, comparison, query, summary
- guide, tutorial, reference, cheat-sheet
- note, draft, idea

### Quality Markers
- debugging, troubleshooting, error-path
- performance, optimization, benchmark
- security, anti-scraping, auth

Rule: every tag on a page must appear in this taxonomy. If a new tag is needed,
add it here first, then use it. This prevents tag sprawl.

## Page Thresholds
- **Create a page** when an entity/concept appears in 2+ sources OR is central to one source
- **Add to existing page** when a source mentions something already covered
- **DON'T create a page** for passing mentions, minor details, or things outside the domain
- **DON'T create a page** for single-use business logic (see purpose.md Rule 1)
- **DON'T create a page** for trivial syntax errors (see purpose.md Rule 2)
- **Split a page** when it exceeds ~200 lines — break into sub-topics with cross-links
- **Archive a page** when its content is fully superseded — move to `wiki/_archive/`, remove from index

## Entity Pages
One page per notable entity (tool, company, person, product, protocol). Include:
- Overview / what it is
- Key facts and dates
- Relationships to other entities ([[wikilinks]])
- Source references

## Concept Pages
One page per concept or topic (e.g., "Agentic RPA", "Shadow-DOM Scraping"). Include:
- Definition / explanation
- Current state of knowledge
- Open questions or debates
- Related concepts ([[wikilinks]])

## Comparison Pages
Side-by-side analyses (e.g., "Selenium vs Playwright", "UiPath vs YinDao"). Include:
- What is being compared and why
- Dimensions of comparison (table format preferred)
- Verdict or synthesis
- Sources

## Note Pages (Personal / Quick Capture)
Quick thoughts, ideas, exploration notes. Minimal frontmatter:
```yaml
---
title: Quick Note Title
created: YYYY-MM-DD
type: note
tags: [note, idea]
---
```
Notes are ephemeral — promote to entity/concept/guide pages when they accumulate enough substance.

## Update Policy
When new information conflicts with existing content:
1. Check the dates — newer sources generally supersede older ones
2. If genuinely contradictory, note both positions with dates and sources
3. Mark the contradiction in frontmatter: `contradictions: [page-name]`
4. Flag for user review in the lint report
