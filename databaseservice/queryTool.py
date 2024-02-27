
# Script to make queries to the database

import mysql.connector
import pandas as pd

##under progress!!
from flask import Flask,jsonify, make_response,request
from flask_restful import Api, Resource
app = Flask(__name__)
api = Api(app)

#EJ klar. Detta är tanken att load recorder ska använda i framtiden för att lägga in Target service data i databasen. 
def add_load_data(load_data):
    try:
        connection = mysql.connector.connect(user='root',  #Connects to Elsa-mysql container and the database simulationDB
                                            password='root',
                                            host='127.0.0.1',
                                            port = '3306',
                                            database = 'simulationDB' 
                                            )
        print("Connected to MySQL database successfully")

        cursor = connection.cursor()
        
        for row,item in load_data.iterrows(): #Skriv om när vi vet dataformen
            cursor.execute("INSERT INTO target_device (timestamp,requests) Values (%s,%s);",(item['time'], item['requests']))

        connection.commit()
        
        cursor.close()


    except mysql.connector.Error as error:
        print("Error while connecting to MySQL:", error)

    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()
            print("MySQL connection closed")

def add_target_load(average_load, total_load,instances_scaled, timestamp):
    try:
        connection = mysql.connector.connect(user='root',  #Connects to Elsa-mysql container and the database simulationDB
                                            password='root',
                                            host='127.0.0.1',
                                            port = '3306',
                                            database = 'simulationDB' 
                                            )

        cursor = connection.cursor()
        cursor.execute("INSERT INTO target_device (average_load,total_load,instances, timestamp) Values (%s,%s,%s,%s);",(average_load, total_load,instances_scaled,timestamp))
        connection.commit()
        cursor.close()


    except mysql.connector.Error as error:
        print("Error while connecting to MySQL:", error)

    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()
            print("MySQL connection closed")

def fetch_and_return_data(start_date):
    db_config = {
        "host": "127.0.0.1",
        "user": "root",
        "password": "root",
        "database": "simulationDB"
    
    }

    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        #Qquert som hämtar allt från worldcup från start_date
        cursor.execute("SELECT timestamp, SUM(requests) as method_count FROM worldcup98 WHERE timestamp LIKE '{}%' GROUP BY timestamp".format(start_date))

        result = cursor.fetchall()
        return result
    
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None
    
    finally:
        if cursor:
            cursor.close()
        if connection.is_connected():
            connection.close()

class DatabaseService(Resource):

    def get(self): ##Override! This is what happens when we send a get request to the Load generator (starts a load)
        start_date = request.json.get('start_date', None)
        if start_date is not None:
            data = fetch_and_return_data(start_date)
            return make_response(jsonify(data), 200)
    
    def post(self):
        total_load = request.json.get('total_load', None)
        average_load = request.json.get('average_load', None)
        instances_scaled = request.json.get('instances_scaled', None)
        timestamp = request.json.get('time', None)
        if total_load is not None:
            add_target_load(average_load, total_load, instances_scaled, timestamp)
        
api.add_resource(DatabaseService, "/databaseservice") 

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0') #Startar flask server för DatabaseService 













    

       # 3 argument annars blir det call error
#    if len(sys.argv) == 3:
#        print("Usage: python queryTool.py start_date resample_frequency")
#        sys.exit(1)

 #   start_date = sys.argv[1]
 #   resample_frequency = sys.argv[2]

 #   data_result = fetch_and_return_data(start_date, resample_frequency)

    # HÄR KAN MAN ANVÄNDA  (DataFrame) I EN ANNAN FUNCTION ELLER PERFORM ADDITIONAL PROCESSING
    #if data_result is not None:
        # här printas bara datan i annat format, ville se hur det såg ut 
    #    for index, row in data_result.iterrows():
    #        print(f"Timestamp: {row['time']}, Requests: {row['method_count']}")