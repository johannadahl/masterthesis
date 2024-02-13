import subprocess
import sys
import os

# Define the command as a list of strings
command = [
    'python3',
    '/app/cbsa_tools/view.py',  # Full path to view.py
    '--dataset', 'WORLDCUP98',
    '--part', 'wc_day90_1',
    '--input', '/app/cbsa_tools/worldcup98.zip',  # Full path to input file
    '--start', '1998-07-24T00:48:00',
    '--duration', '1h',
    '--format', 'json'
]

try:
    print(os.getcwd())
    subprocess.run(command, check=True)
except subprocess.CalledProcessError as e:
    print(f"An error occurred: {e}")