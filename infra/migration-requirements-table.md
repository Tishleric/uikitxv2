# Cloud Migration Requirements for FRGM Dashboard

## Migration Analysis Table

| Application/Feature | Component | Current State | Migration Requirements | Effort | Priority |
|---|---|---|---|---|---:|
| **Data Ingestion** | | | | | |
| Actant Feed | `actant/eod`, `actant/sod` | Direct file processing | • Chicago server pushes CSV to S3<br>• Lambda processes S3 events<br>• Store in Redis/DynamoDB | Low | Critical |
| TT REST API | `TTRestAPI/*` | Direct API calls from app | • Lambda scheduled to snapshot TT data to S3<br>• ECS reads from S3/Redis only<br>• Remove direct `fetch_tt_price` calls | Medium | Critical |
| Pricing Monkey | `pricing_monkey/*` | Web scraping/automation | • Retire in production (as noted)<br>• Historical data only from S3 | None | Low |
| **Data Storage** | | | | | |
| Observatory Logs | `observability.db` | SQLite with decorators | • Keep SQLite on EFS initially<br>• Plan migration to DynamoDB streams<br>• Ensure single writer pattern | Low | High |
| CSV Data Files | `data/input/*`, `data/output/*` | Local filesystem | • All file I/O redirected to S3<br>• Use boto3 for read/write<br>• Update all file paths | High | Critical |
| **Core Dashboard** | | | | | |
| Main App | `apps/dashboards/main/app.py` | Monolithic Dash app | • Containerize with gunicorn<br>• Configure for 0.0.0.0 binding<br>• Environment variables for configs | Low | Critical |
| Scenario Ladder | `scl_*` functions | Reads CSV, calls APIs | • Modify to read from S3<br>• Use Redis for spot prices<br>• Remove PM fetch in prod | Medium | High |
| Greek Analysis | `acp_*` functions | In-memory calculations | • No changes needed<br>• Benefits from high RAM | None | Low |
| Actant EOD | `aeod_*` functions | File-based processing | • Read from S3 instead of local<br>• Cache results in Redis | Medium | High |
| Actant PnL | `actant_pnl/*` | Excel/CSV processing | • S3 for file storage<br>• DynamoDB for results cache | Medium | Medium |
| **Monitoring System** | | | | | |
| Decorators | `lib/monitoring/decorators/*` | SQLite writes | • Add CloudWatch Logs writer<br>• Keep SQLite on EFS for now<br>• Dual-write during transition | Medium | High |
| Performance Tracking | `@monitor()` decorator | Function timing/tracing | • Enhance with X-Ray tracing<br>• Add CloudWatch custom metrics<br>• Preserve existing interface | Low | Medium |
| Circuit Breaker | `circuit_breaker.py` | In-memory state | • Use Redis for state sharing<br>• Enable cross-instance coordination | Medium | Low |
| **Infrastructure** | | | | | |
| Configuration | Hard-coded paths | Local file paths | • Environment variables<br>• Secrets Manager for API keys<br>• Parameter Store for configs | Medium | Critical |

## Key Migration Patterns

### 1. File System → S3
```python
# Current
df = pd.read_csv('data/input/actant.csv')

# Migrated  
s3 = boto3.client('s3')
obj = s3.get_object(Bucket='frgm-data', Key='input/actant.csv')
df = pd.read_csv(obj['Body'])
```

### 2. Direct API → S3 Snapshot
```python
# Current
spot_price = fetch_from_tt_api()

# Migrated
spot_price = redis_client.get('tt:spot:ZN')  # Lambda updates this
```

### 3. SQLite → EFS (Temporary)
```python
# No code change needed
# Mount EFS at /app/logs in container
# Existing SQLite code continues working
```

## Timeline

**Week 1**:
1. Deploy S3 + Lambda + Redis/DynamoDB infrastructure
2. Containerize main app with minimal changes
3. Use EFS for SQLite persistence
4. Deploy with high-RAM Fargate task

**Week 2**:
1. Migrate file I/O to S3
2. Set up Lambda for TT snapshots
3. Testing and deployment
4. Documentation

**Post-Launch**:
1. Optimize RAM usage
2. Migrate decorators to CloudWatch
3. Implement proper autoscaling
4. Cost optimization 