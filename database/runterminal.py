import sys
import json
import pandas as pd



data_list = []
for line in sys.stdin:
    data = json.loads(line)
        # Append the parsed JSON data to the list
    data_list.append(data)
df = pd.DataFrame(data_list)
print(df)
