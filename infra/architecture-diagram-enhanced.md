# Enhanced Architecture Diagram

```mermaid
flowchart LR
    %% On-premises environment
    subgraph "On-Premises"
        A["Chicago Feed Server<br/>(Actant & TT data sources)"]
    end

    %% AWS Cloud (VPC)
    subgraph "AWS Cloud (VPC)"
        S3[(S3 Bucket<br/>Feed Files)]
        L[Lambda<br/>Ingestion Processor]
        L2[Lambda<br/>TT API Snapshots]
        R[(MemoryDB Redis<br/>In-Memory Cache)]
        D[(DynamoDB<br/>Trade Data Store)]
        EFS[(EFS<br/>SQLite Monitoring)]
        E[ECS Fargate<br/>Dashboard Service]
        ALB[(Application Load Balancer)]
        SM(Secrets Manager)
        CW[(CloudWatch<br/>Alarms)]
        CB[(AWS Chatbot<br/>Slack)]
        TT[TT REST API]
    end

    %% Data flow
    A  -- "Push CSV/JSON<br/>files (1-2 s)"     --> S3
    S3 -- "New file event"                       --> L
    L  -- "Parse & store<br/>latest data"        --> R
    L  -- "Persist records"                      --> D
    
    %% TT API Snapshot flow
    CW -- "Schedule trigger<br/>(every 30s)"     --> L2
    L2 -- "Fetch market data"                    --> TT
    L2 -- "Store snapshot"                       --> S3
    L2 -- "Update cache"                         --> R
    
    %% Dashboard queries
    E  -- "Query latest data"                    --> R
    E  -- "Query history"                        --> D
    E  -- "Write monitoring logs"                --> EFS
    
    %% Web traffic
    ALB -- "HTTPS (Dash UI)"                     --> E
    
    %% Secrets flow
    SM -- "API Keys/Secrets"                     --> E
    SM -- "API Keys/Secrets"                     --> L
    SM -- "TT API Credentials"                   --> L2
    
    %% Monitoring
    CW -- "logs/metrics"                         --> L
    CW -- "logs/metrics"                         --> L2
    CW -- "logs/metrics"                         --> E
    CW -- "trigger alerts"                       --> CB
    
    %% Styling
    classDef storage fill:#f9f,stroke:#333,stroke-width:2px
    classDef compute fill:#bbf,stroke:#333,stroke-width:2px
    classDef external fill:#bfb,stroke:#333,stroke-width:2px
    
    class S3,R,D,EFS storage
    class L,L2,E compute
    class A,TT external
```

## Key Enhancements:
1. **EFS for SQLite**: Shows where monitoring logs are stored persistently
2. **TT API Lambda**: Separate Lambda for scheduled TT snapshots (satisfies CTO requirement)
3. **Clear data flow**: No direct ECS → TT API connection
4. **CloudWatch scheduling**: Shows how TT snapshots are triggered 