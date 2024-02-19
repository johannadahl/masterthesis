import sys
import pandas as pd
import time
import requests

# Denna kod itererar över varje tidsenhet som ges i argumentet och printar den sammanlagda loaden över den tiden
# Körs genom python loadGenerator 1998-05 30S (eller liknande)
# OBS kommer köras i alla oändlighet om den inte stängs av!!!

def process_data(data_result, resample_frequency):
    BASE = "http://127.0.0.1:5000/"

    if data_result is not None:
        # kollar varje rad i dataframen och printar värdet med delay som anges
        for index, row in data_result.iterrows():
            print(f"Method count for {index}: {row['method_count']}")

            response = requests.post(BASE+"Workload/"+f"{row['method_count']}") #Skickar en POST request till restAPI med workload! Kommer få ERROR om inte en Flask server är startad
            print(response)
            time.sleep(10) # detta kanske är fusk, borde vara en inparameter

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("MÅSTE SKRIVAS SOM: python loadGenerator.py start_date resample_frequency")
        sys.exit(1)

    start_date = sys.argv[1]
    resample_frequency = sys.argv[2]

    from queryTool import fetch_and_return_data

    data_result = fetch_and_return_data(start_date, resample_frequency)

    process_data(data_result, resample_frequency)

