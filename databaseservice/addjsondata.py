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

        for row,item in df_counts.iterrows():
            send_query(cursor,"INSERT INTO allworldcup98 (timestamp,requests) Values (%s,%s);",(item['time'], item['requests']))

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
        data_list.append(data)

    df = pd.DataFrame(data_list) #Adds all data into a dataframe
    df_counts = df.groupby('time').size().reset_index(name='requests') #preprocess the data into requests/timestammp (in seconds)
  #  print(df)
  #  print(df_counts)
    connect_and_insert_to_sql(df_counts)


if __name__ == '__main__':
    main()
