# AWS Cloud Development Setup Plan - FRGM Dashboard

## Overview
This document outlines the complete plan for deploying the FRGM Dashboard to AWS cloud infrastructure, starting with a development environment and later adapting for production.

## Architecture Summary
- **Data Flow**: Actant (market data) → S3 → Lambda → Redis/DynamoDB → Dashboard
- **TT Integration**: TT API → Lambda → S3 → Redis (working orders only)
- **Dashboard**: ECS Fargate (16-120GB RAM) → EFS (SQLite monitoring)
- **Access**: ALB → HTTPS → Users

## Phase Overview

### Phase 0: AWS Foundation (Day 1-2)
- Account setup & IAM configuration
- Networking (VPC, subnets, security groups)
- Base infrastructure with CDK
- ✓ Checkpoint: Can deploy test Lambda

### Phase 1: Data Pipeline (Day 3-4)
- S3 buckets for feeds
- Lambda for Actant/TT processing
- MemoryDB Redis & DynamoDB setup
- ✓ Checkpoint: File → S3 → Lambda → Redis flow works

### Phase 2: Container Infrastructure (Day 5-6)
- ECR repository & Docker image
- ECS cluster & task definition
- ALB configuration
- EFS for SQLite persistence
- ✓ Checkpoint: Dashboard accessible via ALB

### Phase 3: Monitoring & Automation (Day 7)
- CloudWatch alarms
- Chatbot → Slack integration
- CI/CD pipeline setup
- ✓ Checkpoint: Alerts working, auto-deploy from GitHub

### Phase 4: Code Migration (Week 2)
- File I/O → S3 migration
- Configuration externalization
- Integration testing
- ✓ Checkpoint: Full app working in cloud

## Detailed Phase 1: Data Pipeline

### 1.1 S3 Bucket Setup (2 hours)

**Bucket Structure:**
```
frgm-actant-dev/
  ├── market-data/           # Market data from Actant
  │   └── 2024/01/15/GE_XCME.ZN_20240115_103938.csv
  ├── eod/
  │   └── 2024/01/15/actant_eod_20240115.csv
  ├── sod/
  │   └── 2024/01/15/actant_sod_20240115.csv
  └── processed/
      └── [archived files]

frgm-tt-dev/
  ├── working-orders/        # TT working order snapshots
  │   └── 2024/01/15/orders_snapshot_1705320000.json
  └── processed/
      └── [archived snapshots]

frgm-monitoring-dev/
  └── logs/
      └── [CloudWatch exports if needed]
```

**CDK Implementation:**
```python
# Three separate buckets for data isolation
actant_bucket = s3.Bucket(self, "ActantData",
    bucket_name="frgm-actant-dev",
    lifecycle_rules=[{
        'id': 'archive-old-files',
        'transitions': [{
            'storage_class': s3.StorageClass.GLACIER,
            'transition_after': Duration.days(30)
        }]
    }]
)

tt_bucket = s3.Bucket(self, "TTData", 
    bucket_name="frgm-tt-dev"
)

monitoring_bucket = s3.Bucket(self, "MonitoringData",
    bucket_name="frgm-monitoring-dev"
)
```

**Testing Checkpoint:**
```bash
# Test each bucket
aws s3 cp test-actant.csv s3://frgm-actant-dev/market-data/test.csv
aws s3 cp test-orders.json s3://frgm-tt-dev/working-orders/test.json
# Verify lifecycle policies
aws s3api get-bucket-lifecycle-configuration --bucket frgm-actant-dev
```

### 1.2 Lambda Functions (4 hours)

**Actant Market Data Processor:**
```python
actant_lambda = _lambda.Function(self, "ActantProcessor",
    memory_size=2048,  # 2GB for processing market data
    timeout=Duration.minutes(5),
    environment={
        'REDIS_ENDPOINT': redis_endpoint,
        'DYNAMO_TABLES': json.dumps({
            'market_data': 'ActantMarketData',
            'eod': 'ActantEODData',
            'sod': 'ActantSODData'
        })
    }
)

# S3 event trigger
actant_bucket.add_event_notification(
    s3.EventType.OBJECT_CREATED,
    s3n.LambdaDestination(actant_lambda),
    s3.NotificationKeyFilter(suffix=".csv")
)
```

**TT Working Orders Snapshot Lambda:**
```python
tt_lambda = _lambda.Function(self, "TTSnapshot",
    memory_size=1024,  # 1GB for API calls
    timeout=Duration.minutes(2),
    environment={
        'TT_API_ENDPOINT': 'https://api.tradingtechnologies.com',
        'REDIS_ENDPOINT': redis_endpoint,
        'S3_BUCKET': 'frgm-tt-dev'
    }
)

# CloudWatch Event Rule for scheduling
rule = events.Rule(self, "TTSnapshotSchedule",
    schedule=events.Schedule.rate(Duration.seconds(30))
)
rule.add_target(targets.LambdaFunction(tt_lambda))
```

### 1.3 MemoryDB Redis Setup (2 hours)

**Network Isolation Configuration:**
```python
# Private subnet group
redis_subnet_group = elasticache.CfnSubnetGroup(self, "RedisSubnets",
    subnet_ids=vpc.select_subnets(
        subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT
    ).subnet_ids
)

# Security group - internal access only
redis_sg = ec2.SecurityGroup(self, "RedisSG",
    vpc=vpc,
    description="Redis access from Lambda/ECS only",
    allow_all_outbound=False  # Explicit deny
)

# Only allow specific services
redis_sg.add_ingress_rule(
    peer=lambda_sg,
    connection=ec2.Port.tcp(6379),
    description="Lambda access"
)
redis_sg.add_ingress_rule(
    peer=ecs_sg,
    connection=ec2.Port.tcp(6379),
    description="ECS access"
)

# MemoryDB Cluster
redis_cluster = memorydb.CfnCluster(self, "RedisCluster",
    cluster_name="frgm-dev",
    node_type="db.r6g.large",  # 13GB memory
    num_shards=1,
    num_replicas_per_shard=1,
    subnet_group_name=redis_subnet_group.ref,
    security_group_ids=[redis_sg.security_group_id],
    tls_enabled=True
)
```

**Redis Data Schema:**
```redis
# Actant market data (latest)
HSET "actant:market:ZN" 
  "price" "112.50"
  "timestamp" "1705320000"
  "bid" "112.49"
  "ask" "112.51"
  "volume" "15234"

# TT working orders
HSET "tt:orders:active"
  "order_12345" '{"id":"12345","side":"BUY","qty":10,...}'
  "order_12346" '{"id":"12346","side":"SELL","qty":5,...}'

# Metadata
SET "last_update:actant:market" "1705320000"
SET "last_update:tt:orders" "1705320030"
```

### 1.4 DynamoDB Tables (2 hours)

**Table Definitions:**
```python
tables = {
    'ActantMarketData': {
        'partition_key': 'instrument_id',
        'sort_key': 'timestamp',
        'description': 'Actant market data time series'
    },
    'ActantEODData': {
        'partition_key': 'instrument_id',
        'sort_key': 'timestamp',
        'description': 'End of day positions/Greeks'
    },
    'ActantSODData': {
        'partition_key': 'account_date',
        'sort_key': 'instrument_id',
        'description': 'Start of day positions'
    },
    'TTWorkingOrders': {
        'partition_key': 'order_id',
        'sort_key': 'timestamp',
        'ttl_attribute': 'expire_time',
        'description': 'TT order snapshots with 7-day TTL'
    },
    'PerformanceMetrics': {
        'partition_key': 'function_name',
        'sort_key': 'timestamp',
        'ttl_attribute': 'expire_time',
        'description': 'Future: monitoring migration'
    }
}

for table_name, config in tables.items():
    table = dynamodb.Table(self, table_name,
        table_name=f"{table_name}-dev",
        partition_key=dynamodb.Attribute(
            name=config['partition_key'],
            type=dynamodb.AttributeType.STRING
        ),
        sort_key=dynamodb.Attribute(
            name=config['sort_key'],
            type=dynamodb.AttributeType.STRING 
            if 'instrument' in config['sort_key'] 
            else dynamodb.AttributeType.NUMBER
        ),
        billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
        point_in_time_recovery=True
    )
    
    if 'ttl_attribute' in config:
        table.add_global_secondary_index(
            index_name='ttl-index',
            partition_key=dynamodb.Attribute(
                name='ttl_attribute',
                type=dynamodb.AttributeType.NUMBER
            )
        )
```

### 1.5 Secrets Manager Configuration (1 hour)

```bash
# TT API Credentials
aws secretsmanager create-secret \
    --name "dev/tt-api" \
    --description "TT REST API credentials" \
    --secret-string '{
        "api_key": "YOUR_TT_API_KEY",
        "api_secret": "YOUR_TT_API_SECRET",
        "environment": "live"
    }'

# Redis Auth (if using password)
aws secretsmanager create-secret \
    --name "dev/redis" \
    --description "Redis authentication" \
    --secret-string '{
        "auth_token": "GENERATED_STRONG_PASSWORD"
    }'

# Database credentials (future use)
aws secretsmanager create-secret \
    --name "dev/database" \
    --description "Database connection info" \
    --secret-string '{
        "endpoint": "TO_BE_POPULATED",
        "username": "admin",
        "password": "TO_BE_GENERATED"
    }'
```

### 1.6 Lambda Function Code

**Actant Market Data Processor (`lambda/actant_processor.py`):**
```python
import os
import json
import boto3
import pandas as pd
import redis
from datetime import datetime
from typing import Dict, Any

s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
secrets_client = boto3.client('secretsmanager')

# Get Redis connection
redis_endpoint = os.environ['REDIS_ENDPOINT']
redis_client = redis.Redis(
    host=redis_endpoint,
    port=6379,
    ssl=True,
    decode_responses=True
)

# DynamoDB tables
table_config = json.loads(os.environ['DYNAMO_TABLES'])

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Process Actant market data files from S3."""
    
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        
        # Determine data type from path
        if 'market-data' in key:
            process_market_data(bucket, key)
        elif 'eod' in key:
            process_eod_data(bucket, key)
        elif 'sod' in key:
            process_sod_data(bucket, key)
    
    return {'statusCode': 200, 'body': 'Processing complete'}

def process_market_data(bucket: str, key: str) -> None:
    """Process Actant market data CSV."""
    
    # Read CSV from S3
    obj = s3_client.get_object(Bucket=bucket, Key=key)
    df = pd.read_csv(obj['Body'])
    
    # Store latest in Redis
    for _, row in df.iterrows():
        instrument = row['instrument']
        redis_key = f"actant:market:{instrument}"
        
        redis_client.hset(redis_key, mapping={
            'price': str(row['price']),
            'bid': str(row.get('bid', '')),
            'ask': str(row.get('ask', '')),
            'volume': str(row.get('volume', 0)),
            'timestamp': str(int(datetime.now().timestamp()))
        })
    
    # Store history in DynamoDB
    table = dynamodb.Table(f"{table_config['market_data']}-dev")
    with table.batch_writer() as batch:
        for _, row in df.iterrows():
            batch.put_item(Item={
                'instrument_id': row['instrument'],
                'timestamp': int(datetime.now().timestamp() * 1000),
                **row.to_dict()
            })
    
    # Update metadata
    redis_client.set(
        'last_update:actant:market',
        str(int(datetime.now().timestamp()))
    )
```

**TT Working Orders Snapshot (`lambda/tt_snapshot.py`):**
```python
import os
import json
import boto3
import requests
from datetime import datetime
from typing import Dict, List, Any

s3_client = boto3.client('s3')
secrets_client = boto3.client('secretsmanager')
redis_client = None  # Initialize in handler

def get_tt_credentials() -> Dict[str, str]:
    """Retrieve TT API credentials from Secrets Manager."""
    secret = secrets_client.get_secret_value(SecretId='dev/tt-api')
    return json.loads(secret['SecretString'])

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Fetch TT working orders and store snapshot."""
    
    # Get credentials
    creds = get_tt_credentials()
    
    # Initialize Redis
    global redis_client
    if not redis_client:
        redis_endpoint = os.environ['REDIS_ENDPOINT']
        redis_client = redis.Redis(
            host=redis_endpoint,
            port=6379,
            ssl=True,
            decode_responses=True
        )
    
    # Fetch working orders from TT
    headers = {
        'X-API-KEY': creds['api_key'],
        'X-API-SECRET': creds['api_secret']
    }
    
    response = requests.get(
        f"{os.environ['TT_API_ENDPOINT']}/v1/orders/working",
        headers=headers,
        timeout=30
    )
    
    if response.status_code == 200:
        orders = response.json()
        
        # Store snapshot in S3
        timestamp = int(datetime.now().timestamp())
        s3_key = f"working-orders/{datetime.now().strftime('%Y/%m/%d')}/orders_snapshot_{timestamp}.json"
        
        s3_client.put_object(
            Bucket=os.environ['S3_BUCKET'],
            Key=s3_key,
            Body=json.dumps(orders),
            ContentType='application/json'
        )
        
        # Update Redis with current orders
        redis_client.delete('tt:orders:active')
        for order in orders:
            redis_client.hset(
                'tt:orders:active',
                order['order_id'],
                json.dumps(order)
            )
        
        # Update metadata
        redis_client.set('last_update:tt:orders', str(timestamp))
        
        return {
            'statusCode': 200,
            'body': f'Processed {len(orders)} working orders'
        }
    else:
        print(f"TT API error: {response.status_code} - {response.text}")
        return {
            'statusCode': response.status_code,
            'body': 'Failed to fetch orders'
        }
```

### 1.7 End-to-End Testing Matrix

| Test Case | Input | Expected Output | Validation Method |
|-----------|-------|-----------------|-------------------|
| Actant Market Data | Upload market CSV to S3 | Latest prices in Redis | `redis-cli HGETALL actant:market:ZN` |
| Actant EOD Flow | Upload EOD CSV to S3 | Data in DynamoDB | Query DynamoDB table |
| TT Order Snapshot | CloudWatch trigger | Orders in Redis + S3 | Check Redis hash + S3 file |
| Network Isolation | External Redis access | Connection timeout | `redis-cli -h <endpoint>` from outside |
| Error Handling | Malformed CSV | Error in CloudWatch | Check Lambda logs |
| High Volume | 50 files rapidly | All processed | Monitor CloudWatch metrics |

## Manual vs Automated Setup

### Manual Steps (Human Required)
1. **AWS Account Creation**
   - Sign up at https://aws.amazon.com
   - Provide credit card and contact info
   - Phone verification required

2. **IAM Setup**
   - Create admin user (not root)
   - Enable MFA on admin account
   - Save access credentials securely

3. **External Integrations**
   - TT API key generation (https://api.tradingtechnologies.com)
   - Slack workspace OAuth (for CloudWatch alerts)
   - GitHub repository secrets (for CI/CD)

4. **Domain/Certificate (Optional)**
   - Route 53 domain registration
   - ACM certificate validation

### Automated via CDK/Scripts
- All infrastructure (VPC, subnets, security groups)
- Lambda functions and triggers
- Redis and DynamoDB setup
- S3 buckets and policies
- CloudWatch alarms
- ECS/Fargate configuration

## Cost Estimates

### Development Environment (Monthly)
- S3: ~$20 (storage + requests)
- Lambda: ~$5 (2-3M invocations)
- MemoryDB: ~$140 (db.r6g.large)
- DynamoDB: ~$10 (on-demand)
- ECS Fargate: ~$870 (16 vCPU, 120GB RAM)
- ALB: ~$20
- **Total: ~$1,065/month**

### Production Environment (Monthly)
- Same as dev but:
- ECS Fargate: 2x tasks for HA (~$930)
- Additional monitoring/backups: ~$50
- **Total: ~$1,145/month**

## Success Criteria

### Phase 1 Complete When:
- [ ] S3 buckets receiving files from Chicago
- [ ] Lambda processing files within 2 seconds
- [ ] Redis contains latest market data
- [ ] DynamoDB storing historical data
- [ ] TT orders updating every 30 seconds
- [ ] All resources in private network
- [ ] Secrets properly managed
- [ ] CloudWatch showing healthy metrics

### Next Steps
After Phase 1 validation, proceed to Phase 2 (Container Infrastructure) to deploy the dashboard application. 