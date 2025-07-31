import os

file_path = "data/reference/net_position_streaming (4).csv"
line_count = 0
with open(file_path, 'r') as f:
    for line in f:
        line_count += 1

print(f"The file '{file_path}' has {line_count} lines (including header).")
