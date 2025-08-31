## Actant Spot Risk Archiver - Windows Service Setup

### Paths
- Source: `C:\Users\ceterisparibus\Documents\Next\uikitxv2\data\input\actant_spot_risk`
- Archive: `C:\Users\ceterisparibus\Documents\HistoricalMarketData`

### Config
Edit `configs/actant_spot_risk_archiver.yaml` if paths or thresholds need changing.

### Run once (foreground)
```
python scripts\run_actant_spot_risk_archiver.py --config configs\actant_spot_risk_archiver.yaml
```

### Install as a Windows Service (NSSM)
1. Download NSSM and place `nssm.exe` somewhere in PATH.
2. Run:
```
nssm install ActantSpotRiskArchiver "C:\\Python310\\python.exe" "Z:\\uikitxv2\\scripts\\run_actant_spot_risk_archiver.py" --config "Z:\\uikitxv2\\configs\\actant_spot_risk_archiver.yaml"
```
3. Set Startup type to Automatic.
4. Recovery: Restart the Service on first and second failure.

### Logs and Ledger
- Logs: `%PROGRAMDATA%\ActantArchive\logs\archive.log`
- CSV ledger (daily): `%PROGRAMDATA%\ActantArchive\ledger\ledger_YYYY-MM-DD.csv`

### Safety Notes
- The service moves whole day-folders older than today via atomic rename (fast).
- Today’s folder remains; files move once ≥ 60 minutes old and unchanged across scans.
- If interrupted, it resumes safely. No code changes needed to existing pipeline.

