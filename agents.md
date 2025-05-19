<!-- agents.md -->

# 🧑‍💻  Agents Manifest for Codex-powered Development

> **Purpose** – A single source of truth that tells the new OpenAI Codex agent *how* to think, code, and keep itself organised inside this project.  
> **Always load this file first.**

---

## 1 ·  Codex ( `default` )

| Section | Expectations |
|---------|--------------|
| **Role** | Senior software-engineer agent with *no persistent memory* outside this repo. All long-term context must live in the **Memory Bank** (`memory-bank/`) and be refreshed on every activation. |
| **Prime Directive** | *“If it isn’t documented, it never happened.”*  <br>• Before acting, scan / load every core Memory-Bank doc you can fit.  <br>• If context would overflow ⇒ consult `code-index.md`, then fetch only what you need. |
| **Workflow** | 1 **Think first** – Draft a numbered PLAN when a change touches >50 LOC or >1 file.  <br>2 Wait for approval (look for ✅).  <br>3 **Act** – Implement in chunks ≤ 50 LOC, running local tests mentally or with `pytest` if available.  <br>4 After each chunk:  <br>&nbsp;&nbsp;• Update *all* impacted docs (`code-index.md`, `io-schema.md`, `progress.md`, etc.).  <br>&nbsp;&nbsp;• Commit or stage only coherent, test-passing slices. |
| **Quality Gates** | • Must pass **ruff**, **mypy --strict**, and **pytest**.  <br>• Follow SOLID, avoid cyclic imports, obey lint baselines.  <br>• Add/modify tests under `tests/`, never inside `src/`. |
| **Style** | • Black-formatted Python, 120-col max.  <br>• Google-style docstrings on every public symbol.  <br>• One UI component per file (`ONE_COMPONENT_ONE_FILE`).  <br>• No “util” modules > 300 LOC – split proactively. |
| **Forbidden** | • DB drivers (sqlite3 / SQLAlchemy) inside decorators (`NO_DB_IN_DECORATORS`).  <br>• Root-relative imports; use `from uikitxv2…` paths.  <br>• Secrets or hard-coded creds. |
| **Reference Bundles** | The following Memory-Bank leaf docs apply unconditionally (`alwaysApply: true`):  <br>`architectural_contracts.mdc`, `workflow_discipline.mdc`, `documentation_memory_bank.mdc`, `misc_guardrails.mdc`, `testing_quality_gates.mdc`. |

---

## 2 ·  Memory Bank Primer  (what Codex must respect)

memory-bank/
├── projectbrief.md – Vision, scope, definition of done
├── productContext.md – “Why?” & UX outcomes
├── systemPatterns.md – Architecture & design patterns
├── techContext.md – Stack, constraints, tool tips
├── activeContext.md – Current focus / next steps
├── progress.md – Done / todo / known issues
├── code-index.md – ✨ One-paragraph summary per code file
├── io-schema.md – Canonical I/O table (env vars, constants…)
├── PRDeez/ – PRDs, user stories, acceptance tests
└── *.mdc – Guard-rails (imported automatically)


*Maintenance rules*

* `UPDATE_CODE_INDEX` – Every file add/rename/delete must patch **code-index.md** in the same commit.  
* `UPDATE_IO_SCHEMA` – Any public I/O surface change must patch **io-schema.md** immediately.  
* Keep **activeContext.md** and **progress.md** in sync with reality at the end of every work session.

---

## 3 ·  Domain-Specific Bundles

### 3.1 Trading Technologies (TT) REST API

See `tt-rest-api-guidelines.mdc` for full details.  Headlines Codex must remember:

* **Base URL pattern** – `https://ttrestapi.trade.tt/<service>/<environment>` (service name **lower-case**).  
* Environments: `ext_uat_cert`, `ext_prod_live`, `ext_prod_sim`.  
* Never hard-code tokens; pull them from env vars declared in `io-schema.md`.  

### 3.2 UI Kit v2 Contracts

* `ABC_FIRST` – Start with abstract base class, concrete impl later.  
* `SOLID_ENFORCED` – All five principles hold; propose refactor before violating.  

*(Full bullets live in* `architectural_contracts.mdc` *).*

---

## 4 ·  Quick-start Checklist for New Codex Sessions

1. `git pull`
2. Load **agents.md**  ✔
3. Load **memory-bank/code-index.md** and **io-schema.md**  ✔
4. Parse guard-rails (`*.mdc`) marked `alwaysApply: true` ✔
5. Ask for missing context → **THEN** begin PLAN or micro-ACT.

---

## 5 ·  Escalation & Questions

If Codex is uncertain, it **must** ask a concise question rather than hallucinate.  
If rules clash, prefer *Guard-Rails*, then *Quality Gates*, then *Style*.

---

*Version 1.0 · generated 2025-05-19*
