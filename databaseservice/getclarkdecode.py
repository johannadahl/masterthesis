import sys
import mysql.connector

def execute_query(cursor, query):
    cursor.execute(query)

def is_utf8(text):
    try:
        text.encode('utf-8').decode('utf-8')
        return True
    except UnicodeDecodeError:
        return False

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
            # Check if the entire query has good characters
            if is_utf8(query):
                execute_query(cursor, query)
            else:
                print(f"Skipping query with bad characters: {query}")

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
            line = line.decode('utf-8')
        except UnicodeDecodeError:
            print(f"Ignoring line with non-UTF-8 characters: {line}")
            continue

        query = line.strip()
        if query:
            queries.append(query)

    connect_and_insert_to_sql(queries)

if __name__ == '__main__':
    main()
