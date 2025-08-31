# Gamma Ladder (Notebook Conversion)

This folder contains a direct conversion of the teammate-provided Jupyter notebook `gamma shop ladder.ipynb` into a runnable Python script, preserving the original code as-is as much as possible.

- Source notebook: `gamma shop ladder.ipynb`
- Converted script: `gamma_ladder.py`

Usage

- Run the script directly:

```
python gamma_ladder_standalone/gamma_ladder.py
```

- Or double-click the batch file:

```
gamma_ladder_standalone/run_gamma_ladder.bat
```

The batch launcher requires Python in PATH and mapped drives `Y:` and `Z:`.

Notes
- Paths and constants (e.g., `Y:\\Archive`, `Z:\\Hanyu\\FiveMinuteMonkey`, output HTML path) are preserved from the original notebook.
- Minimal structural changes were made solely to place the code into a `.py` file.
