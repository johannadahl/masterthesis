
# Script som hämtar  DataFrame som är returnerad av fetch_and_return_data och tar ett medelvärde
# medelvärdet är för den tidsramen man kör koden i
# Denna kod anropas som följande: 
# python simpleOperationTest.py 1998-05 40S
# där 1998-05 är vilken månad man vill titta på 
# där 40S är hur många sekunder den klumpar ihop. går att köra 10S eller vad man nu vill 


import sys
import pandas as pd

def process_data(data_result):
    if data_result is not None:
        # kör en mean bara för att se om det funkar 
        mean_value = data_result['method_count'].mean()

        print(f"Mean value of 'method_count': {mean_value}")


if __name__ == "__main__":
    #  från queryTool-scriptet 

    if len(sys.argv) != 3:
        print("Usage: python process_data.py start_date resample_frequency")
        sys.exit(1)

    start_date = sys.argv[1]
    resample_frequency = sys.argv[2]

    # Importera query tool
    from queryTool import fetch_and_return_data

    data_result = fetch_and_return_data(start_date, resample_frequency)

    # Kallar på process_data med datan från fetch-funktionen
    process_data(data_result)
