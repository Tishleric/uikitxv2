We are restarting a different project with an improved approach. we are moving slowly but securely. as we move forward, i will append the next step for you to execute to the bottom of this brief.

uikitxv2/                              ← repo root
│
├── pyproject.toml                   ← build, deps, ruff+mypy+pytest cfg
├── README.md                        ← install, "why", quick-start
├── .gitignore
├── .pre-commit-config.yaml          ← ruff ▸ mypy ▸ black ▸ pytest
│
├── src/                             ← **importable package lives here**
│   └── uikitxv2/
│       ├── __init__.py
│       │
│       ├── core/                    ← ABCs & cross-cutting contracts
│       │   ├── base_component.py
│       │   ├── base_decorator.py
│       │   ├── logger_protocol.py
│       │   └── errors.py
│       │
│       ├── components/              ← Dash/Plotly one-liners
│       │   ├── __init__.py
│       │   ├── tabs.py
│       │   ├── button.py
│       │   ├── combobox.py
│       │   ├── radiobutton.py
│       │   ├── listbox.py
│       │   ├── grid.py
│       │   └── graph.py
│       │
│       ├── decorators/              ← SQLite-logging wrappers
│       │   ├── __init__.py
│       │   ├── performance/
│       │   │   ├── __init__.py
│       │   │   ├── cpu.py           # trace_cpu
│       │   │   ├── query.py         # trace_query_perf
│       │   │   └── memory.py        # trace_memory
│       │   │
│       │   ├── data/
│       │   │   ├── __init__.py
│       │   │   └── calls.py         # trace_data_calls
│       │   │
│       │   └── movement/
│       │       ├── __init__.py
│       │       └── checkpoint.py    # checkpoint decorator
│       │
│       ├── db/                      ← thin persistence layer
│       │   ├── __init__.py
│       │   ├── models.py
│       │   └── session.py
│       │
│       ├── utils/
│       │   └── colour_palette.py
│       │
│       └── __about__.py             ← version, author, etc.
│
├── demo/                            ← runnable showcase
│   ├── app.py                       # Dash app using wrapped components
│   ├── mock_data.py                 # fake DF / random generator
│   ├── expected_trace.json          # golden decorator output
│   └── README.md                    # how to run & what to look for
│
├── examples/                        ← **human-readable code snippets**
│   ├── basic_usage.py               # < 25 LOC each
│   ├── theme_override.py
│   └── README.md                    # index of snippets
│
├── tests/                           ← unit + integration (outside package)
│   ├── components/
│   ├── decorators/
│   ├── db/
│   ├── demo/                        # compares SQLite rows ↔ expected_trace.json
│   └── conftest.py
│
└── memory-bank/                     ← Cursor's long-term memory
    ├── projectbrief.md
    ├── productContext.md
    ├── systemPatterns.md
    ├── techContext.md
    ├── activeContext.md
    ├── progress.md
    ├── code-index.md               # ← moved here
    ├── io-schema.md
    ├── notionSync.md
    ├── .cursorrules
    └── PRDeez/                     # user stories / acceptance
