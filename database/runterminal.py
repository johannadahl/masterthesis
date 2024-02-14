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
        data = json.loads(line)
            # Append the parsed JSON data to the list
        data_list.append(data)
    df = pd.DataFrame(data_list)
    df_counts = df.groupby('time').size().reset_index(name='requests')
    print(df)
    print(df_counts)



if __name__ == '__main__':
    main()
