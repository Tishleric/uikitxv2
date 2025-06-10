# FRGM Trade Accelerator - Unified Dashboard Platform

## Project Status: **PRODUCTION READY** ✅

A comprehensive unified trading dashboard platform that successfully consolidates 5 separate trading applications into a single, professional interface with 8-item sidebar navigation.

## Current Architecture (January 2025)

```
uikitxv2/                              ← repo root
│
├── pyproject.toml                     ← build, deps, ruff+mypy+pytest cfg
├── README.md                          ← install, "why", quick-start
├── .gitignore
│
├── lib/                               ← main installable package (pip install -e .)
│   ├── __init__.py                    ← package exports/re-exports
│   │
│   ├── components/                    ← Dash/Plotly UI components
│   │   ├── __init__.py
│   │   ├── basic/                     ← Simple components
│   │   │   ├── button.py, checkbox.py, combobox.py
│   │   │   ├── container.py, listbox.py, rangeslider.py
│   │   │   ├── radiobutton.py, tabs.py, toggle.py
│   │   │   └── tooltip.py
│   │   ├── advanced/                  ← Complex components
│   │   │   ├── datatable.py, graph.py
│   │   │   ├── grid.py, mermaid.py
│   │   │   └── loading.py
│   │   ├── core/                      ← Component foundations
│   │   │   ├── base_component.py
│   │   │   └── protocols.py
│   │   └── themes/                    ← UI theming
│   │       └── colour_palette.py
│   │
│   ├── monitoring/                    ← Performance monitoring
│   │   ├── decorators/                ← Tracing decorators
│   │   │   ├── context_vars.py, trace_time.py
│   │   │   ├── trace_closer.py, trace_cpu.py
│   │   │   └── trace_memory.py
│   │   └── logging/                   ← Logging configuration
│   │       ├── config.py
│   │       └── handlers.py
│   │
│   └── trading/                       ← Trading business logic
│       ├── common/                    ← Shared utilities
│       │   ├── price_parser.py
│       │   └── date_utils.py
│   │
│   ├── actant/                    ← Actant integration
│   │   ├── eod/                   ← End-of-day processing
│   │   └── sod/                   ← Start-of-day processing
│   │
│   ├── pricing_monkey/            ← PM automation
│   │   ├── automation/, retrieval/, processors/
│   │
│   ├── tt_api/                    ← TT REST API
│   │
│   ├── ladder/                    ← Ladder functionality
│   │
│   └── bond_future_options/       ← BFO pricing engine
│
├── apps/                              ← Application layer
│   ├── dashboards/
│   │   ├── main/                      ← **UNIFIED DASHBOARD** (port 8052)
│   │   │   └── app.py                 ← Main application (5,383 lines)
│   │   ├── actant_eod/                ← Original EOD dashboard (reference)
│   │   ├── actant_preprocessing/      ← Greek analysis dashboard
│   │   └── ladder/                    ← Scenario ladder dashboard
│   │
│   └── demos/                         ← Demo applications
│
├── scripts/                           ← Utility scripts
│   ├── actant_eod/                    ← EOD processing scripts
│   └── actant_sod/                    ← SOD processing scripts
│
├── data/                              ← Data organization
│   ├── input/                         ← Input data (eod/, sod/, ladder/)
│   └── output/                        ← Output data (eod/, sod/, ladder/)
│
├── tests/                             ← Unit + integration tests
│   ├── components/, monitoring/, trading/
│   └── integration/
│
├── memory-bank/                       ← Project documentation
│   ├── activeContext.md, progress.md
│   ├── code-index.md, io-schema.md
│   └── PRDeez/                        ← User stories
│
├── SumoMachine/                       ← Standalone automation tools
└── TTRestAPI/                         ← TT API examples and tools
```

## Navigation System (8 Items) 🗂️

The unified dashboard provides professional sidebar navigation to all trading tools:

1. 💰 **Pricing Monkey Setup** - Bond future options pricing with automation
2. 📊 **Analysis** - Market movement analytics with real-time data
3. 📈 **Greek Analysis** - CTO-validated options pricing engine
4. 📚 **Project Documentation** - Interactive project documentation
5. 📊 **Scenario Ladder** - Advanced trading ladder with TT API integration
6. 📈 **Actant EOD** - Complete end-of-day trading analytics dashboard
7. 📋 **Logs** - Performance monitoring and flow trace analytics
8. 🔗 **Mermaid** - Interactive architecture diagrams

## Import Pattern

All components use clean package imports after `pip install -e .`:

```python
from components import Button, ComboBox, DataTable, Graph
from monitoring.decorators import TraceTime, TraceCpu, TraceMemory
from trading.pricing_monkey import run_pm_automation
from trading.actant.eod import ActantDataService
```

## Current Status

**✅ PRODUCTION READY**: Complete unified trading platform with all objectives achieved

- **Zero Regression**: All original functionality preserved
- **Professional UI**: Consistent theming and elegant navigation
- **Performance Monitoring**: Comprehensive trace decorators
- **Scalable Architecture**: Ready for future enhancements
- **Production Quality**: Battle-tested and fully operational

## Entry Points

- **Main Application**: `python apps/dashboards/main/app.py` (port 8052)
- **Individual Dashboards**: Available for reference/testing
- **Scripts**: Data processing and automation utilities
