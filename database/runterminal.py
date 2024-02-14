import sys
import json
# Read input from stdin
for line in sys.stdin:
    # Process each line as needed
    data = json.loads(line)
    
    # Access and print the value associated with the key "time"
    print(data["time"])