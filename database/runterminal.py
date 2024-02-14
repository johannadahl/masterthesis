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
                                            database = 'Elsa_Containers'
                                            )
        print("Connected to MySQL database successfully")

        cursor = connection.cursor()
        send_query(cursor, "select * from worldcup_requests;",0)
        # Fetch all rows from the result set
        rows = cursor.fetchall()
        for row in rows:
            print(row)
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
