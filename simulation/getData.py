import mysql.connector
import pandas as pd

def fetch_and_return_data():
    db_config = {
        "host": "127.0.0.1",
        "user": "root",
        "password": "root",
        "database": "johannasDB"
    }

    try:
        #Connect to database
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        #Qquert som hämtar allt från #johannas_table
        cursor.execute("SELECT time, SUM(request_count) as method_count FROM johannas_table GROUP BY time")
        result = cursor.fetchall()

        #skapar en DataFrame
        column_names = ["time", "method_count"]
        df = pd.DataFrame(result, columns=column_names)

        #vill se hur datan ser ut, ska tas bort så fort det är mycket data!!
        print(df)
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

    # Now you can use data_result (DataFrame) in another function or perform additional processing
    if data_result is not None:
        # här printas bara datan i annat format, ville se hur det såg ut 
        for index, row in data_result.iterrows():
            print(f"Timestamp: {row['time']}, Requests: {row['method_count']}")