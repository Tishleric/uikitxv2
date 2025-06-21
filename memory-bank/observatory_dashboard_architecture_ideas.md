# Observatory Dashboard - Architecture Brainstorm

*This document stores conceptual diagrams brainstormed for the future evolution of the Observatory Dashboard. These are not final designs but represent architectural ideas for features like filtering, drill-downs, and data flow.*

## Filtering & Drill-Down Architecture

```mermaid
graph TD
    subgraph "High-Level View"
        A[Observatory Table] -->|Click Row| B{Details Modal}
    end

    subgraph "Drill-Down"
        B --> C[View Source Code]
        B --> D[View Child Traces]
        B --> E[View Performance History]
    end

    subgraph "Filtering"
        F[Filter Controls] --> A
        F -- "Process, Status, Time" --> A
    end
```

## Technical Architecture

```mermaid
graph TD
    subgraph "Frontend (Dash)"
        A[Dashboard UI] -->|HTTP Request| B[DataService]
    end

    subgraph "Backend (Python)"
        C[@monitor Decorator] --> D[ObservatoryQueue]
        D --> E[BatchWriter]
        E --> F[SQLite Database]
        B --> F
    end

    subgraph "Data Flow"
        C -- "Captures data" --> D
        D -- "Buffers data" --> E
        E -- "Writes data" --> F
        B -- "Queries data" --> F
    end
```

## User Journey Flow

```mermaid
sequenceDiagram
    participant User
    participant Dashboard
    participant Database

    User->>Dashboard: Clicks "Refresh"
    Dashboard->>Database: Get trace data
    Database-->>Dashboard: Return latest traces
    Dashboard-->>User: Display traces

    User->>Dashboard: Clicks on a row
    Dashboard->>Dashboard: Show details modal
    Dashboard->>Database: Get specific trace details
    Database-->>Dashboard: Return details
    Dashboard-->>User: Display source code & metrics
``` 