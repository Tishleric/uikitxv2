# live‑risk‑observability/projectbrief.md  
_Version 0.2 • 17 Jun 2025 • Author: Observability‑Strategy‑GPT_

---

## 0 • Change Log  
| Date | Author | Note |
|------|--------|------|
| 16 Jun 2025 | O‑SGPT | Initial brief v0.1 delivered |
| 17 Jun 2025 | O‑SGPT | **Added strict column spec (Process / Data / Data Type / Data Value / Timestamp / Status / Exception)**, refined DB schema, aligned UI to Dash (not React), clarified dependency‑graph buffs |

---

## 1 • Business Goal & Success Criteria  
1. **Detect** any unhandled exception or stale market‑data feed in < 10 s.  
2. **Display** every function call and every input/output variable as a **row with seven canonical columns**:  

   | Process | Data | Data Type | Data Value | Timestamp | Status | Exception |  

   *One row **per variable**; `Data Type` ∈ {`INPUT`,`OUTPUT`}; `Status` ∈ {`OK`,`ERR`}.*  
3. **Empower a new engineer** to trace a data path and reproduce an issue inside 15 min.  
4. **Ship MVP** in ≤ 10 developer‑days (Cursor‑assisted).  

---

## 2 • Solution Overview  

```mermaid
graph LR
    code[Python functions & Dash callbacks] --> |@monitor| Q(core_queue)
    Q --> DB[(SQLite WAL → 6 h ring buffer)]
    DB --> API[FastAPI endpoint for Dash]
    API --> VIEW1[Trace Table (7 cols)]
    API --> VIEW2[Dependency Graph]
    API --> VIEW3[Drill‑down Modal]
    DB -- rules --> ALERT[Slack / PagerDuty]

All components run in‑process today; OTLP emitter & external stores are phased upgrades.

3 • Technical Spec
3.1 Decorator (lib/monitoring/decorators/monitor.py)
@monitor(
    process_group: str,              # logical grouping
    sample: float = 1.0,             # 0–1 for hot‑path sampling
    mask: tuple[str, ...] = (),      # fields whose repr is hashed
    log_inputs: bool = True,
    log_outputs: bool = True,
    otel_span: bool = False          # Phase‑2 flag
)

Uses inspect.signature() to bind arg names → values.

Emits one process_trace row and N data_trace rows
(N = inputs*log_inputs + outputs*log_outputs).

Exceptions are trapped → status='ERR', exception holds traceback.

3.2 SQLite Schema (logs/core_logs.db)


CREATE TABLE process_trace (
  ts           TEXT  NOT NULL,
  process      TEXT  NOT NULL,      -- dotted function/class
  status       TEXT  NOT NULL,      -- OK | ERR
  duration_ms  REAL  NOT NULL,
  exception    TEXT,                -- full traceback or NULL
  PRIMARY KEY (ts, process)
);

CREATE TABLE data_trace (
  ts          TEXT  NOT NULL,
  process     TEXT  NOT NULL,
  data        TEXT  NOT NULL,       -- variable name
  data_type   TEXT  NOT NULL,       -- INPUT | OUTPUT
  data_value  TEXT  NOT NULL,       -- repr() or <HASHED>
  status      TEXT  NOT NULL,       -- copy from parent row
  exception   TEXT,                 -- copy from parent row
  PRIMARY KEY (ts, process, data, data_type)
);
-- 6‑hour retention
CREATE INDEX idx_data_ts ON data_trace(ts);

Rolling purge (executed each 60 s by retention_worker.py):
DELETE FROM process_trace WHERE ts < datetime('now','-6 hours');
DELETE FROM data_trace    WHERE ts < datetime('now','-6 hours');

3.3 Dash UI (Python, not React)
All Dash code under apps/dashboards/observability/.

| Component            | Key Features                                                                                                            | Notes                                                    |
| -------------------- | ----------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------- |
| **Trace Table**      | Paginated <br/> Filter: date‑range, process, data, “Errors only” <br/> Color pills for Status                           | Uses `dash.DataTable` with virtualisation                |
| **Drill‑down Modal** | Left: syntax‑highlighted `inspect.getsource` <br/> Right: sparkline of last‑30 min `duration_ms`                        | Kick off with `dcc.Graph` + cached PNG                   |
| **Dependency Graph** | Dash‑Cytoscape force‑layout <br/> Nodes: processes (square), feeds (circle)<br/> Edges red if last update > 2× interval | **Buffs**: hover tooltip with last latency & error count |
| **Status Ribbon**    | QueueDepth, SQLiteWriteLag, LastFeedUpdate badges                                                                       | Colour tokens defined in `_theme.py`                     |


Dummy screenshots (sent earlier) used React; this Dash build must emulate the same visual hierarchy while leveraging Bootstrap v5 dark theme (dbc.themes.DARKLY).

3.4 Alert Rules (MVP)
| Name                | Condition                        | Action                               |
| ------------------- | -------------------------------- | ------------------------------------ |
| Unhandled Exception | `status='ERR'` row inserted      | POST to `/webhook` (Slack/PagerDuty) |
| Feed Lag            | `now - last_update(feed) > 10s`  | Same                                 |
| Queue Backpressure  | `core_queue.qsize()>5k` for 30 s | Warning banner only                  |

3.5 Libraries & Versions
| Purpose     | Library                                         | Version           |
| ----------- | ----------------------------------------------- | ----------------- |
| UI          | dash, dash‑cytoscape, dash‑bootstrap‑components | 2.16.*, 1.*, 1.\* |
| Alerts      | httpx                                           | 0.27.\*           |
| Future OTLP | opentelemetry‑api / sdk                         | 1.25.\*           |
| Testing     | pytest, pytest‑asyncio                          | latest            |

4 • Implementation Roadmap
| Phase            | Scope                                                                           | Deliverables                          | Effort               | Owners             |
| ---------------- | ------------------------------------------------------------------------------- | ------------------------------------- | -------------------- | ------------------ |
| **0. Prep**      | Credential cleanup, merge multiple `logs/*.db`                                  | `.env` + single `core_logs.db`        | **S**                | Alice              |
| **1. MVP**       | Decorator, queue writer, schema, Dash views, 2 alert rules                      | Running on sandbox & integration      | **M** (≈ 8 dev‑days) | Bob (dev) + Cursor |
| **2. OTEL**      | `otel_span=True`, OTEL Collector (Docker), Prometheus, Grafana dashboard import | Dual‑write traces, Grafana live       | **M**                | Charlie            |
| **3. Hardening** | S3 archival, sampling heuristics, SLO dashboards, self‑monitoring               | 30‑day cold store, burn‑rate alerting | **L**                | Bob                |

T‑shirt: S < 0.5 d ; M ≈ 2 d ; L ≈ 4 d.

5 • Testing Matrix
| Test                 | Env            | Expected                                          |
| -------------------- | -------------- | ------------------------------------------------- |
| Decorator happy‑path | unit           | 1 `process_trace` + N `data_trace` rows           |
| Decorator exception  | unit           | `status='ERR'` row, Slack mock fired              |
| Queue overflow       | integration    | Warning badge red, no crash                       |
| 6‑h purge            | time‑warp unit | Rows older than 6 h deleted                       |
| End‑to‑end UI        | integration    | Clicking table row opens modal with matching code |

6 • Open Questions for CTO
Latency budget per decorator call (<15 µs OK?)

Regulatory retention—is 6 h in hot store sufficient before Phase‑3 archival?

RBAC for Dash “Observability” tab—public to all devs or restricted?

Future transport—should we plan for Kafka/Redpanda or stick to OTLP/Prometheus?

7 • Appendix
7.1 Colour Tokens (_theme.py)
TOKENS = {
  "bg": "#0d1117",
  "accent": "#3e8ef7",
  "ok": "#2dc26b",
  "err": "#e55353",
  "stale": "#f0ad4e"
}

7.2 Minimal @monitor Implementation (30 LOC)
def monitor(process_group: str, sample: float = 1.0, mask=(), log_inputs=True, log_outputs=True, otel_span=False):
    def deco(fn):
        qual = f"{fn.__module__}.{fn.__qualname__}"
        @functools.wraps(fn)
        def wrap(*a, **kw):
            if sample < 1.0 and random.random() > sample:
                return fn(*a, **kw)
            start = time.time(); exc = None
            try:
                res = fn(*a, **kw); return res
            except Exception:
                exc = traceback.format_exc(); raise
            finally:
                dur = (time.time()-start)*1e3
                now = datetime.utcnow().isoformat(' ', 'seconds')
                core_queue.put(("process", now, qual, process_group,
                                "ERR" if exc else "OK", dur, exc))
                if log_inputs:
                    for n,v in inspect.signature(fn).bind_partial(*a, **kw).arguments.items():
                        core_queue.put(("data", now, qual, n, "INPUT",
                                        _safe_repr(n, v, mask), "ERR" if exc else "OK", exc))
                if log_outputs and 'res' in locals():
                    core_queue.put(("data", now, qual, "return", "OUTPUT",
                                    _safe_repr("return", res, mask), "ERR" if exc else "OK", exc))
        return wrap
    return deco

Queue consumer maps record type → appropriate INSERT.