"""
Cleans and corrects the net position streaming CSV file by ensuring
it has a proper trailing newline, fixing parsing issues.
"""

from pathlib import Path

SOURCE_CSV = Path("data/reference/net_position_streaming (4).csv")
CLEANED_CSV = Path("data/reference/net_position_streaming_CLEANED.csv")

def clean_csv():
    """
    Reads the source CSV and writes it back to a new file, which
    automatically corrects any missing final newline characters.
    """
    print(f"Reading source file: {SOURCE_CSV}")
    with open(SOURCE_CSV, 'r') as infile:
        content = infile.read()

    print(f"Writing cleaned file to: {CLEANED_CSV}")
    with open(CLEANED_CSV, 'w', newline='') as outfile:
        outfile.write(content)
        # Ensure there's a newline at the very end
        if not content.endswith('\n'):
            outfile.write('\n')
            
    print("File cleaning complete.")

if __name__ == "__main__":
    clean_csv()
