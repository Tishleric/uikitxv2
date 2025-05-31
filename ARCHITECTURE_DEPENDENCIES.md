# UIKitXv2 Architecture Dependency Map

## Overview

This document provides a comprehensive map of file dependencies in the UIKitXv2 project. The architecture follows a layered approach with clear separation of concerns.

## Architecture Layers

### 1. Core Layer (Foundation)
The core layer provides abstract base classes and protocols that define contracts for the rest of the system.

**Files:**
- `src/core/base_component.py` - Abstract base class for all UI components
- `src/core/data_service_protocol.py` - Protocol defining data service interface
- `src/core/mermaid_protocol.py` - Protocol for Mermaid diagram components
- `src/core/logger_protocol.py` - Referenced in architectural contracts

**Dependencies:** None (foundation layer)

### 2. Utilities Layer
Provides shared utilities and theme management.

**Files:**
- `src/utils/colour_palette.py` - Centralized theme and styling definitions
- `src/decorators/context_vars.py` - Shared context variables for decorators

**Dependencies:** None (foundation utilities)

### 3. UI Components Layer
14 reusable UI components that inherit from BaseComponent.

**Files:**
- `src/components/button.py`
- `src/components/checkbox.py`
- `src/components/combobox.py`
- `src/components/container.py`
- `src/components/datatable.py`
- `src/components/graph.py`
- `src/components/grid.py`
- `src/components/listbox.py`
- `src/components/mermaid.py`
- `src/components/radiobutton.py`
- `src/components/rangeslider.py`
- `src/components/tabs.py`
- `src/components/toggle.py`
- `src/components/__init__.py` - Exports all components

**Common Dependencies:**
- All components → `BaseComponent` (except Mermaid)
- `Mermaid` → `MermaidProtocol`
- All components → `colour_palette.py` (for theming)

### 4. Decorator Layer
Provides logging and monitoring decorators following a specific stacking order.

**Files:**
- `src/decorators/trace_closer.py` - Outermost decorator, handles context initialization
- `src/decorators/trace_time.py` - Timing decorator
- `src/decorators/trace_cpu.py` - CPU usage monitoring
- `src/decorators/trace_memory.py` - Memory usage monitoring

**Dependencies:**
- All decorators → `context_vars.py`
- `trace_closer.py` → `logging_config.py`

**Recommended stacking order:** 
```python
@TraceCloser()      # Outermost
@TraceMemory()      
@TraceCpu()         
@TraceTime()        # Innermost
def my_function():
    pass
```

### 5. Logging System
Handles structured logging to SQLite databases.

**Files:**
- `src/lumberjack/logging_config.py` - Logging configuration
- `src/lumberjack/sqlite_handler.py` - Custom SQLite logging handler

**Dependencies:**
- `sqlite_handler.py` → `logging_config.py`

### 6. Data Services Layer

#### ActantEOD Services
Handles end-of-day trading data analysis.

**Files:**
- `ActantEOD/data_service.py` - Main data service implementation
- `ActantEOD/file_manager.py` - JSON file management
- `ActantEOD/data_integrity_check.py` - Data validation
- `ActantEOD/process_actant_json.py` - JSON processing utilities
- `ActantEOD/pricing_monkey_retrieval.py` - PM data retrieval via browser automation
- `ActantEOD/pricing_monkey_processor.py` - PM data processing

**Dependencies:**
- `data_service.py` → `DataServiceProtocol`, `pricing_monkey_retrieval.py`, `pricing_monkey_processor.py`
- `pricing_monkey_retrieval.py` → `pMoneySimpleRetrieval.py`
- `file_manager.py` → `process_actant_json.py`

#### ActantSOD Services
Handles start-of-day operations.

**Files:**
- `ActantSOD/actant.py` - Core SOD functionality
- `ActantSOD/browser_automation.py` - Browser automation utilities
- `ActantSOD/futures_utils.py` - Futures contract utilities
- `ActantSOD/pricing_monkey_adapter.py` - PM data adaptation
- `ActantSOD/pricing_monkey_to_actant.py` - PM to Actant conversion

**Dependencies:**
- `actant.py` → `futures_utils.py`
- `pricing_monkey_adapter.py` → `futures_utils.py`
- `pricing_monkey_to_actant.py` → `pricing_monkey_adapter.py`, `actant.py`, `pMoneySimpleRetrieval.py`
- `browser_automation.py` → `pMoneySimpleRetrieval.py`

#### Pricing Monkey Module
Handles Pricing Monkey integration.

**Files:**
- `src/PricingMonkey/pMoneyAuto.py` - PM automation
- `src/PricingMonkey/pMoneyMovement.py` - Market movement data
- `src/PricingMonkey/pMoneySimpleRetrieval.py` - Simple data retrieval

**Dependencies:** Internal module dependencies only

#### TT REST API
Trading Technologies REST API integration.

**Files:**
- `TTRestAPI/token_manager.py` - Token lifecycle management
- `TTRestAPI/tt_utils.py` - Utility functions
- `TTRestAPI/tt_config.py` - Configuration
- `TTRestAPI/api_example.py` - Example usage

**Dependencies:**
- `token_manager.py` → `tt_utils.py`, `tt_config.py`
- `api_example.py` → `token_manager.py`

### 7. Application Layer
End-user applications built on top of all other layers.

#### Main Dashboard (`dashboard/dashboard.py`)
**Dependencies:**
- UI: All components via `src/components/__init__.py`
- Decorators: `TraceCloser`, `TraceTime`, `TraceCpu`, `TraceMemory`
- Data: `pMoneyAuto.py`, `pMoneyMovement.py`
- Logging: `logging_config.py`

#### ActantEOD Dashboard (`ActantEOD/dashboard_eod.py`)
**Dependencies:**
- UI: All components via `src/components/__init__.py`
- Data: `data_service.py`, `file_manager.py`
- Theme: `colour_palette.py`

#### Demo Applications
- `demo/app.py` - Demo dashboard with all decorators
- `demo/flow.py` - Trading flow demo with context vars
- `demo/query_runner.py` - Query demo with timing

#### Other Applications
- `ladderTest/scenario_ladder_v1.py` - Ladder testing app
- `ladderTest/zn_price_tracker_app.py` - Price tracking app

## Key Architectural Patterns

### 1. Protocol/Interface Pattern
- `DataServiceProtocol` defines interface for data services
- `ActantDataService` implements the protocol
- Enables dependency injection and testability

### 2. Abstract Base Class Pattern
- `BaseComponent` provides common functionality for all UI components
- Ensures consistent API across components

### 3. Decorator Pattern
- Stackable decorators for cross-cutting concerns
- Clear separation of monitoring/logging from business logic

### 4. Centralized Theme Management
- All styling flows through `colour_palette.py`
- Consistent look and feel across the application

### 5. Module Aliasing (Import Strategy)
- Dashboard uses `sys.modules['uikitxv2'] = src` for imports
- Components use relative imports within the package
- Prevents circular dependencies

## Dependency Rules

1. **No Circular Dependencies** - Enforced by architectural contracts
2. **Core Layer Independence** - Core protocols have no dependencies
3. **Decorator Independence** - Decorators only depend on context_vars and logging
4. **Component Independence** - Components only depend on core and utils
5. **Application Layer** - Can depend on any lower layer

## File Count Summary

- Core Layer: 4 files
- Utilities: 2 files  
- UI Components: 14 files
- Decorators: 4 files
- Logging: 2 files
- Data Services: 19 files
- Applications: 7 files
- TT REST API: 4 files

**Total architectural components: ~56 primary files**

## Visualization

See `architecture_dependency_diagram.html` for an interactive Mermaid diagram showing all dependencies. 