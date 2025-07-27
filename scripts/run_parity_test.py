#!/usr/bin/env python3
import subprocess
import sys

# Run the test and capture output
result = subprocess.run(
    [sys.executable, 'scripts/test_parity_simple.py'],
    capture_output=True,
    text=True,
    cwd=r'Z:\uikitxv2'
)

# Print results
print("STDOUT:")
print(result.stdout)
print("\nSTDERR:")
print(result.stderr)
print(f"\nReturn code: {result.returncode}")

# Save to file
with open('parity_test_output.txt', 'w') as f:
    f.write("STDOUT:\n")
    f.write(result.stdout)
    f.write("\n\nSTDERR:\n")
    f.write(result.stderr)

print("\nOutput saved to parity_test_output.txt") 