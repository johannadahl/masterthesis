import mysql.connector
import json
import os
from datetime import datetime, timedelta


# Här är lite queries för att lägga in data i en databas (även om timestamps fattas)
# Ska inte användas på mycket data om inte print-satsen tas bort
# Bör också användas en try except om det är mycket data

mydb = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password="root",
    database="johannasDB"
)

mycursor = mydb.cursor()

# finns sedan innan, detta kan tas bort sen!!!!
mycursor.execute("DROP TABLE IF EXISTS johannas_table")

mycursor.execute("""
    CREATE TABLE johannas_table (
        time TIMESTAMP NOT NULL,
        request_count INT NOT NULL DEFAULT 0,
        PRIMARY KEY (time)
    )
""")
mydb.commit()

directory_path = '/Users/johannadahl/'
os.chdir(directory_path)
file_path = 'johannaTest.txt'
timestamps_from_file = set()

with open(file_path, 'r') as file:
    for line in file:
    
        json_data = json.loads(line)
        time = json_data['time']
        timestamps_from_file.add(time)

        mycursor.execute("SELECT COUNT(*) FROM johannas_table WHERE time = %s", (time,))
        count = mycursor.fetchone()[0]

        if count > 0:
            mycursor.execute("UPDATE johannas_table SET request_count = request_count + 1 WHERE time = %s", (time,))
        else:
            mycursor.execute("INSERT INTO johannas_table (time, request_count) VALUES (%s, 1)", (time,))

mydb.commit()

min_timestamp = min(timestamps_from_file)
max_timestamp = max(timestamps_from_file)

# VAR TVUNGEN ATT GÖRAS OM PGA TYPEERROR här finns säkert nåt smidigare sätt
min_timestamp = datetime.strptime(min_timestamp, "%Y-%m-%dT%H:%M:%S")
max_timestamp = datetime.strptime(max_timestamp, "%Y-%m-%dT%H:%M:%S")

current_timestamp = min_timestamp

while current_timestamp <= max_timestamp:
    mycursor.execute("SELECT COUNT(*) FROM johannas_table WHERE time = %s", (current_timestamp,))
    count = mycursor.fetchone()[0]

    #om timestamp inte finns, lägg till i output ändå
    if count == 0:
        mycursor.execute("INSERT INTO johannas_table (time, request_count) VALUES (%s, 0)", (current_timestamp,))

    current_timestamp += timedelta(seconds=1)

mydb.commit()


mycursor.execute("SELECT * FROM johannas_table")
result = mycursor.fetchall()

#detta är för test, kan tas bort senare så att det inte blir en miljon rader prints
for row in result:
    print(row)

mycursor.close()
mydb.close()
