import sys
import json
import pandas as pd
import mysql.connector 

def send_query(cursor, query, values):
    if values != 0:
        cursor.execute(query,values)
    else: 
        cursor.execute(query)

def print_result(cursor):
    rows = cursor.fetchall()
    for row in rows:
        print(row)


def main():

    data_list = []
    for line in sys.stdin:
        data = json.loads(line) #Reads in the json lines from the terminal output
        data_list.append(data)

    df = pd.DataFrame(data_list) #Adds all data into a dataframe
    df_counts = df.groupby('time').size().reset_index(name='requests') #preprocess the data into requests/timestammp (in seconds)
    print(df)
    print(df_counts)

    try:
        connection = mysql.connector.connect(user='root', 
                                            password='root',
                                            host='127.0.0.1',
                                            port = '3306',
                                            database = 'simulationDB'
                                            )
        print("Connected to MySQL database successfully")

        cursor = connection.cursor()
                # finns sedan innan, detta kan tas bort sen!!!!
        cursor.execute("DROP TABLE IF EXISTS worldcup98_table")

        cursor.execute("""
            CREATE TABLE worldcup98_table (
                timestamp TIMESTAMP NOT NULL,
                requests INT NOT NULL DEFAULT 0,
                PRIMARY KEY (timestamp)
            )
        """)

        for row,item in df_counts.iterrows():
            send_query(cursor,"INSERT INTO worldcup98_table (timestamp,requests) Values (%s,%s);",(item['time'], item['requests']))

        connection.commit()
        
        cursor.close()


    except mysql.connector.Error as error:
        print("Error while connecting to MySQL:", error)

    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()
            print("MySQL connection closed")



if __name__ == '__main__':
    main()
