#Not finished
#The script adds data to the database from json files
import mysql.connector 
import json
import pandas as pd


def send_query(cursor, query, values):
    if values != 0:
        cursor.execute(query,values)
    else: 
        cursor.execute(query)

def print_result(cursor):
    rows = cursor.fetchall()
    for row in rows:
        print(row)

def main2():
    try:

        connection = mysql.connector.connect(user='root', 
                                            password='root',
                                            host='127.0.0.1',
                                            port = '3306',
                                            database = 'Elsa_Containers'
                                            )
        print("Connected to MySQL database successfully")

        cursor = connection.cursor()

        #Connect to Elsa_containers database, to access test tables
        send_query(cursor, "USE Elsa_Containers;",0)
        
        #Access the JSON data
        with open('worldcupdata.json','r') as f:
            data = json.load(f)
        print(data)

        df = pd.DataFrame(data)
        df_counts = df.groupby('time').size().reset_index(name='requests')

        #df['time'] = pd.to_datetime(df['time']) 
        print(df)
        print(df_counts)
        
        for row,item in df_counts.iterrows():
            send_query(cursor,"INSERT INTO worldcup_requests (timestamp,requests) Values (%s,%s);",(item['time'], item['requests']))

        send_query(cursor, "select * from worldcup_requests;",0)
        print_result(cursor)

        #commit changes to add to database
        connection.commit()


    except mysql.connector.Error as error:
        print("Error while connecting to MySQL:", error)

    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()
            print("MySQL connection closed")



def main():
    print("Dockercontainer körs")
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
