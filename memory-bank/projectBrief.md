We are restarting a different project with an improved approach. we are moving slowly but securely. as we move forward, i will append the next step for you to execute to the bottom of this brief.

uikitxv2/                              ← repo root
│
├── pyproject.toml                   ← build, deps, ruff+mypy+pytest cfg
├── README.md                        ← install, "why", quick-start
├── .gitignore
├── decorators_overview.md           ← summary of available decorators
│
├── src/                             ← package source code
│   ├── __init__.py
│   │
│   ├── core/                        ← ABCs & cross-cutting contracts
│   │   ├── __init__.py
│   │   └── base_component.py
│   │
│   ├── components/                  ← Dash/Plotly UI components
│   │   ├── __init__.py
│   │   ├── tabs.py
│   │   ├── button.py
│   │   ├── combobox.py
│   │   ├── radiobutton.py
│   │   ├── listbox.py
│   │   ├── grid.py
│   │   ├── graph.py
│   │   └── datatable.py
│   │
│   ├── decorators/                  ← Logging & tracing decorators
│   │   ├── __init__.py
│   │   ├── context_vars.py
│   │   ├── trace_time.py
│   │   ├── trace_closer.py
│   │   ├── trace_cpu.py
│   │   └── trace_memory.py
│   │
│   ├── lumberjack/                  ← Logging configuration
│   │   ├── __init__.py
│   │   ├── logging_config.py
│   │   └── sqlite_handler.py
│   │
│   └── utils/
│       ├── __init__.py
│       └── colour_palette.py
│
├── demo/                            ← runnable showcase
│   ├── app.py                       # Dash app using wrapped components
│   ├── flow.py                      # Demo flow implementation
│   ├── query_runner.py              # Query execution engine
│   ├── queries.yaml                 # Sample queries
│   ├── run_queries_demo.py          # Demo runner script
│   └── test_decorators.py           # Decorator usage demo
│
├── tests/                           ← unit + integration tests
│   ├── components/                  ← UI component tests
│   │   ├── test_button_render.py
│   │   ├── test_combobox_render.py
│   │   ├── test_datatable_render.py
│   │   ├── test_graph_render.py
│   │   ├── test_grid_render.py
│   │   ├── test_listbox_render.py
│   │   ├── test_radiobutton_render.py
│   │   └── test_tabs_render.py
│   │
│   ├── decorators/                  ← Decorator tests
│   │   ├── conftest.py
│   │   ├── test_trace_time.py
│   │   ├── test_trace_closer.py
│   │   ├── test_trace_cpu.py
│   │   └── test_trace_memory.py
│   │
│   ├── lumberjack/                  ← Logging tests
│   │   ├── test_logging_config.py
│   │   └── test_sqlite_handler.py
│   │
│   └── conftest.py                  ← Shared test fixtures
│
└── memory-bank/                     ← Cursor's long-term memory
    ├── projectBrief.md
    ├── productContext.md
    ├── systemPatterns.md
    ├── techContext.md
    ├── activeContext.md
    ├── progress.md
    ├── code-index.md
    ├── io-schema.md
    ├── notionSync.md
    ├── .cursorrules
    └── PRDeez/                     # user stories / acceptance
