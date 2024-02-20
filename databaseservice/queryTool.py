
# Script to make queries to the database

import mysql.connector
import pandas as pd
import sys

##under progress!!w

def fetch_and_return_data(start_date, resample_frequency):
    db_config = {
        "host": "127.0.0.1",
        "user": "root",
        "password": "root",
        "database": "simulationDB"
    }

    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        #Qquert som hämtar allt från #worldcup från MAJ MÅNAD
        cursor.execute("SELECT timestamp, SUM(requests) as method_count FROM worldcup98 WHERE timestamp LIKE '{}%' GROUP BY timestamp".format(start_date))

        result = cursor.fetchall()
       # print("Raw data from the database:")
       # print(result)

        column_names = ["time", "method_count"]
        df = pd.DataFrame(result, columns=column_names)

        # Detta är för per 10:e sekund! ska göras om till en egen function sen 
        df['time'] = pd.to_datetime(df['time'])
        df_10_seconds = df.set_index('time').resample(resample_frequency).sum()


        print("First 15 values in the resampled DataFrame:", df_10_seconds.head())
        return df_10_seconds

        #vill se hur datan ser ut, ska tas bort så fort det är mycket data!!
        #print(df)
        #print (" first 15 values in the database ")
        #print (df.head(15))
        #return df
    

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

    finally:
        if cursor:
            cursor.close()
        if connection.is_connected():
            connection.close()

if __name__ == "__main__":
  #  data_result = fetch_and_return_data()  #Endast detta stod här innan!!!

       # 3 argument annars blir det call error
    if len(sys.argv) != 3:
        print("Usage: python queryTool.py start_date resample_frequency")
        sys.exit(1)

    start_date = sys.argv[1]
    resample_frequency = sys.argv[2]

    data_result = fetch_and_return_data(start_date, resample_frequency)

    # HÄR KAN MAN ANVÄNDA  (DataFrame) I EN ANNAN FUNCTION ELLER PERFORM ADDITIONAL PROCESSING
    #if data_result is not None:
        # här printas bara datan i annat format, ville se hur det såg ut 
    #    for index, row in data_result.iterrows():
    #        print(f"Timestamp: {row['time']}, Requests: {row['method_count']}")