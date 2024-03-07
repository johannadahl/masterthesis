import sys
import mysql.connector

def execute_query(cursor, query):
    cursor.execute(query)

def connect_and_insert_to_sql(queries):
    try:
        connection = mysql.connector.connect(
            user='root',
            password='root',
            host='127.0.0.1',
            port='3306',
            database='johanna_testar_dump'
        )
        print("Connected to MySQL database successfully")

        cursor = connection.cursor()

        for query in queries:
            try:
                execute_query(cursor, query)
            except UnicodeDecodeError as decode_error:
                print(f"Skipping line with decoding error: {decode_error}")
                continue

        connection.commit()

    except mysql.connector.Error as error:
        print("Error while connecting to MySQL:", error)

    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()
            print("MySQL connection closed")

def main():
    queries = []
    for line in sys.stdin:
        try:
            line = line.encode('utf-8')
        except UnicodeDecodeError as decode_error:
            print(f"Skipping line with decoding error: {decode_error}")
            continue

        query = line.strip()
        if query:
            queries.append(query)

    connect_and_insert_to_sql(queries)

if __name__ == '__main__':
    main()
