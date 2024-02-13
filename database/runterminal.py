import subprocess
import sys
import os

# Define the command as a list of strings
command = [
    'python3',
    '/home/administrator/cbsa_tools/view.py',  # Full path to view.py
    '--dataset', 'WORLDCUP98',
    '--part', 'wc_day90_1',
    '--input', '/home/administrator/cbsa_tools/worldcup98.zip',  # Full path to input file
    '--start', '1998-07-24T00:48:00',
    '--duration', '1h',
    '--format', 'json'
]

# Run the command using subprocess
try:
    subprocess.run(command, check=True)
except subprocess.CalledProcessError as e:
    print(f"An error occurred: {e}")