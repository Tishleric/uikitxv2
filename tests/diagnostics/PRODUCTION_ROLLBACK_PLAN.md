# Production Rollback Plan

## Current State
- **Original file**: `lib/trading/market_prices/price_updater_service.py`
- **Optimized file**: `tests/diagnostics/price_updater_service_optimized.py`
- **Changes**: Deduplication + batch commits

## Deployment Steps

### 1. Pre-deployment Backup
```bash
# Backup current production file
cp lib/trading/market_prices/price_updater_service.py \
   lib/trading/market_prices/price_updater_service.py.backup_$(date +%Y%m%d_%H%M%S)
```

### 2. Deploy Optimized Version
```bash
# Copy optimized version to production location
cp tests/diagnostics/price_updater_service_optimized.py \
   lib/trading/market_prices/price_updater_service.py
```

### 3. Restart Service
```bash
# Restart the price updater service
# (specific command depends on your deployment)
```

## Rollback Procedure

### If Issues Detected:

1. **IMMEDIATE ROLLBACK** (< 30 seconds):
```bash
# Restore original version
cp lib/trading/market_prices/price_updater_service.py.backup_* \
   lib/trading/market_prices/price_updater_service.py

# Restart service
```

2. **Verify Rollback**:
- Check dashboard updates are flowing
- Monitor latency returns to previous levels
- Confirm no errors in logs

## Monitoring Checklist

### After Deployment:
- [ ] Dashboard "live px" updates working
- [ ] Latency < 1 second per message
- [ ] No errors in price_updater logs
- [ ] Database writes successful
- [ ] Redis messages being consumed

### Warning Signs (trigger rollback):
- ❌ Dashboard prices not updating
- ❌ Errors in logs about missing prices
- ❌ Database lock errors
- ❌ Memory usage spike
- ❌ Service crashes

## Key Differences to Note

### Original Implementation:
- Processes all rows (including duplicates)
- Individual commits per update
- ~18 seconds per message

### Optimized Implementation:
- Deduplicates futures symbols
- Single batch commit
- ~0.2 seconds per message
- Logs deduplication stats

## Emergency Contacts
[Add your team's contact info here]