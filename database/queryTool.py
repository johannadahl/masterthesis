
# Script to make queries to the database

import mysql.connector
import pandas as pd

##under progress!!

def fetch_and_return_data():
    db_config = {
        "host": "127.0.0.1",
        "user": "root", # ändra 
        "password": "root", # ändra
        "database": "simulationDB" # ändra
    }

    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        #Qquert som hämtar allt från #johannas_table
        cursor.execute("SELECT timestamp, SUM(requests) as method_count FROM worldcup98 GROUP BY timestamp")
        result = cursor.fetchall()

        #skapar en DataFrame
        column_names = ["time", "method_count"]
        df = pd.DataFrame(result, columns=column_names)

        #vill se hur datan ser ut, ska tas bort så fort det är mycket data!!
        #print(df)
        print (" first 15 values in the database", df.head())
        return df


    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

    finally:
        if cursor:
            cursor.close()
        if connection.is_connected():
            connection.close()

if __name__ == "__main__":
    data_result = fetch_and_return_data()

    # HÄR KAN MAN ANVÄNDA  (DataFrame) I EN ANNAN FUNCTION ELLER PERFORM ADDITIONAL PROCESSING
    #if data_result is not None:
        # här printas bara datan i annat format, ville se hur det såg ut 
    #    for index, row in data_result.iterrows():
    #        print(f"Timestamp: {row['time']}, Requests: {row['method_count']}")