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
        # Connect to the database
        connection = mysql.connector.connect(**db_config)

        # Create a cursor object
        cursor = connection.cursor()

        # Execute a query to fetch data (replace 'your_table' with your actual table name)
        cursor.execute("SELECT time, SUM(request_count) as method_count FROM johannas_table GROUP BY time")

        # Fetch all the rows
        result = cursor.fetchall()

        # Create a DataFrame from the fetched data
        column_names = ["time", "method_count"]
        df = pd.DataFrame(result, columns=column_names)

        # Print the DataFrame
        print(df)

        return df

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

    finally:
        # Close the cursor and connection
        if cursor:
            cursor.close()
        if connection.is_connected():
            connection.close()

if __name__ == "__main__":
    data_result = fetch_and_return_data()

    # Now you can use data_result (DataFrame) in another function or perform additional processing
    if data_result is not None:
        # Example: Print the result in another format
        for index, row in data_result.iterrows():
            print(f"Timestamp: {row['time']}, Requests: {row['method_count']}")