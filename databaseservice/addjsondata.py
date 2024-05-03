#OBSERVERA detta är inte en del av vårt system!
#Denna körs bara när man vill skicka vidare scrapead data från cbsa_tools in i databasen

#Script that pipeas output from terminal, this is found in sys.stdin (in our case, it is json output)
#Connects and inserts to a mysql connected database

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

def connect_and_insert_to_sql(df_counts):
    try:
        connection = mysql.connector.connect(user='root',  #Connects to Elsa-mysql container and the database simulationDB
                                            password='root',
                                            host='127.0.0.1',
                                            port = '3306',
                                            database = 'simulationDB' 
                                            )
        print("Connected to MySQL database successfully")

        cursor = connection.cursor()
        
        # Code-part below is outcommented since it is only necessary if the table doesnt exist in the database yet (first time running the code).  
        
    #    cursor.execute("DROP TABLE IF EXISTS tablename")

     #   cursor.execute("""
     #       CREATE TABLE allworldcup98 (
      #          timestamp TIMESTAMP NOT NULL,
      #          requests INT NOT NULL DEFAULT 0,
      #          PRIMARY KEY (timestamp)
       #     )
       # """)

        for index, row in df_counts.iterrows():
            timestamp = row['timestamp']
            requests = row['requests']
            send_query(cursor, "INSERT INTO counter_strike2 (timestamp, requests) VALUES (%s, %s);", (timestamp, requests))

        connection.commit()
        
        cursor.close()


    except mysql.connector.Error as error:
        print("Error while connecting to MySQL:", error)

    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()
            print("MySQL connection closed")



def main():

    data_list = []
    for line in sys.stdin:
        data = json.loads(line)
        for timestamp, requests in data:
            data_list.append({'timestamp': pd.to_datetime(timestamp, unit='ms'), 'requests': requests})
    df = pd.DataFrame(data_list)
    df_counts = df.groupby('timestamp').sum().reset_index()  # Group by 'timestamp' and sum the requests
     ##Prediktions kommer per 60:e min, här resamplar vi för att få varje minut
    df_counts.set_index('timestamp', inplace=True)
    upsampled_df = df_counts.resample('T').mean()

    #Interpolering för att få punkter mellan punkter
    interpolated_df = upsampled_df.interpolate(method='linear')
    print("i generate predictions", interpolated_df)

    connect_and_insert_to_sql(interpolated_df)


if __name__ == '__main__':
    main()
