# Knowledge Base Evolution Guide (Purpose & Boundaries)

> Master RPA + AI integration workflows and strategy patterns — making diverse agent tools genuinely productive in daily engineering practice.
>
> Last updated: 2026-05-14

This is the top-level constraint for Hermes Agent's LLM Wiki architecture. Every implicit observation, knowledge capture, and incremental compilation step must be judged against the scope and boundaries defined here.

---

## 1. Core Knowledge Domains (Scope)

As an **RPA Engineer**, incremental capture targets these five high-value dimensions only:

### 1.1 Research & Horizon
- **Scope**: Cutting-edge AI Agent architectures (MCP protocol, LangChain, etc.), LLM-RPA convergence paths (Agentic RPA), computer vision for DOM-less element scraping.
- **Capture focus**: Technology trend analysis, industry insights, cross-disciplinary connections, long-term tech stack evaluation.

### 1.2 Personal Synthesis
- **Scope**: Career retrospectives, productivity workflow methodology, algorithm practice notes, system design thinking, personal tech debt log.
- **Capture focus**: Internalized core concepts, stripped-down causal chains (no filler), personal cognitive upgrade models.

### 1.3 Technical Knowledge Base
- **Scope**: Mainstream RPA tools (YinDao, UiPath, Automation Anywhere), programming languages (Python, JavaScript), automation engines (Selenium, Playwright), databases, API architecture.
- **Capture focus**: Syntax quirks, implicit API design patterns, anti-scraping mechanisms under high concurrency, non-trivial exception handling patterns.

### 1.4 Scenario Solutions
- **Scope**: Cross-platform data reconciliation, high-precision PDF/OCR VAT invoice extraction flows, complex SAP automation, Windows dynamic handle hijacking.
- **Capture focus**: Converting one-off client-specific business logic into **reusable scenario architecture design patterns**.

### 1.5 RPA Production & Delivery
- **Scope**: Unattended robot stability guarantees, multi-thread scheduling queue design, RPA logging and dashboard auditing, enterprise-grade credential management.
- **Capture focus**: Complete multi-branch troubleshooting trails (Err -> Fix -> Err -> Fix full path), core bug avoidance guides, performance edge-case tuning.

---

## 2. Boundary Rules (Hard Constraints)

### Rule 1: Reusable Patterns Only — No Single-Use Business Logic
- **Forbidden**: Recording client-private data, single-project-specific fields, or one-off business logic (e.g., "张三's financial report.xlsx").
- **Required**: Strip the business shell, extract and compile into a reusable architecture pattern page (e.g., generalize a specific form-filling script into `[[Excel-to-Web-Form-Automation]]`).

### Rule 2: Deep Error Paths Only — No Trivial Mistakes
- **Forbidden**: Recording syntax errors from missing parentheses, typos, or transient network disconnects.
- **Required**: Record multi-branch debugging value blockers (e.g., Chrome upgrade breaking legacy XPath, ultimately solved via JS Shadow-DOM piercing — compile into `[[Shadow-DOM-Element-Scraping]]`).

### Rule 3: Structured Inbox First, Strictly Gated Tags
- **All implicit captures** enter `000_Inbox/` with frontmatter tag `implicit-capture`.
- Pages only graduate to `wiki/concepts/`, `wiki/entities/`, etc. after review and de-duplication against existing content.
- **Forbidden**: Inventing new top-level tags outside the SCHEMA.md taxonomy. New tags must be proposed to the user or added to the taxonomy first.

---

## 3. Evolution Protocol

When the user's focus shifts or new scenarios emerge, this file updates via:

### Explicit Mode
When the user gives a clear instruction (e.g., "Add a new domain: I'm diving into Xiaohongshu/Douyin anti-scraping RPA account automation"), parse and modify the Core Knowledge Domains section without asking for confirmation — just report what changed.

### Implicit Mode
When Hermes detects an undefined topic appearing more than 5 times in 2 weeks, during the next lint run it proactively suggests an update. Only executes after user confirmation ("yes").

---

## 4. Language Policy

All wiki content in `wiki/` and `000_Inbox/` processed pages **must be written in Chinese** — Raw source material in `raw/` retains its original language.
