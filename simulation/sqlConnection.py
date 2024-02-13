

import mysql.connector
import json
import os

mydb = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password="root",
    database="johannasDB"
)

mycursor = mydb.cursor()

#detta är mest för testningen!!
mycursor.execute("DROP TABLE IF EXISTS johannas_table")


mycursor.execute("""
    CREATE TABLE johannas_table (
        time TIMESTAMP NOT NULL,
        request_count INT NOT NULL DEFAULT 1,
        PRIMARY KEY (time)
    )
""")

mydb.commit()

directory_path = '/Users/johannadahl/'
os.chdir(directory_path)
file_path = 'johannaTest.txt'

with open(file_path, 'r') as file:
    for line in file:
        # beror på vilket format detta är i 
        json_data = json.loads(line)
        time = json_data['time']
        # kollar att inte timestampet redan finns i boordeet
        mycursor.execute("SELECT COUNT(*) FROM johannas_table WHERE time = %s", (time,))
        count = mycursor.fetchone()[0]

        if count > 0:
            mycursor.execute("UPDATE johannas_table SET request_count = request_count + 1 WHERE time = %s", (time,))
        else:
            mycursor.execute("INSERT INTO johannas_table (time) VALUES (%s)", (time,))
mydb.commit()

mycursor.execute("SELECT * FROM johannas_table")
result = mycursor.fetchall()

mycursor.close()
mydb.close()
