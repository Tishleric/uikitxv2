RosettaStone Standalone Bundle

This folder is a self-contained bundle for the RosettaStone symbol translator. It includes:

- rosetta_stone.py and strike_converter.py
- data/reference/symbol_translation/ExpirationCalendar_CLEANED.csv

No external repo imports are required. The CSV path is resolved relative to this folder.

Requirements

- Python 3.9+
- pandas

Install:

```
pip install pandas
```

Quickstart

From this folder:

```
python quickstart_rosetta.py
```

or run the comprehensive demo:

```
python usage_examples.py
```

This runs a comprehensive set of translations across all supported formats.

CLI

```
python translate_cli.py --from actantrisk --to bloomberg --symbol "XCME.VY3.21JUL25.111:75.C"
```

Programmatic usage

```
from rosetta_stone import RosettaStone

rs = RosettaStone()  # uses local CSV in ./data/reference/symbol_translation/ExpirationCalendar_CLEANED.csv

# Example: ActantRisk -> Bloomberg
print(rs.translate("XCME.VY3.21JUL25.111:75.C", "actantrisk", "bloomberg"))
```

Notes
- For standalone execution, rosetta_stone.py will import strike_converter.py via a relative import and fallback to local import if needed.
- The bundled CSV is a full copy of the calendar used by translations.
