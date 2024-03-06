import re
from collections import defaultdict
import json

log_file_path = "/Users/johannadahl/Documents/masterthesis/databaseservice/clarknet_data"

# Extract timestamps and count requests per second
timestamp_counts = defaultdict(int)

with open(log_file_path, 'r', encoding='latin-1') as log_file:
    for line in log_file:
        match = re.search(r'\[([\w:/]+\s[+\-]\d{4})\]', line)
        if match:
            timestamp = match.group(1)
            # Remove the "-0400" from the timestamp
            timestamp = timestamp.replace(" -0400", "")
            timestamp_counts[timestamp] += 1
        else:
            print(f"Line does not match the pattern: {line.strip()}")

# Create a list of dictionaries for each timestamp and request count
result_list = [{'timestamp': timestamp, 'count': count} for timestamp, count in timestamp_counts.items()]

# Save the result to a JSON file
with open('log_data.json', 'w') as json_file:
    json.dump(result_list, json_file, indent=2)

print("JSON file created: log_data.json")

