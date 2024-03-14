
# Script to make queries to the database

import mysql.connector
import pandas as pd
from datetime import timedelta
from flask import Flask,jsonify, make_response,request
from flask_restful import Api, Resource
app = Flask(__name__)
api = Api(app)

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

##Aktuell!!
def add_target_service_load(applied_load, experienced_load, current_time, instances):
    try:
        connection = mysql.connector.connect(user='root',  #Connects to Elsa-mysql container and the database simulationDB
                                            password='root',
                                            host='127.0.0.1',
                                            port = '3306',
                                            database = 'simulationDB' 
                                            )

        cursor = connection.cursor()
        cursor.execute("INSERT INTO target_service (TIMESTAMP, appliedLoad,experiencedLoad, instances) Values (%s,%s,%s,%s);",
                       (current_time, applied_load, experienced_load, instances))
        connection.commit()
        cursor.close()


    except mysql.connector.Error as error:
        print("Error while connecting to MySQL:", error)

    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()
            print("MySQL connection closed")
def fetch_and_return_data(databasename,start_date,end_date):
    db_config = {
        "host": "127.0.0.1",
        "user": "root",
        "password": "root",
        "database": "simulationDB"
    
    }

    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        #Qquert som hämtar allt från worldcup från start_date tom end_date
        cursor.execute("SELECT timestamp, SUM(requests) as method_count FROM {} WHERE timestamp BETWEEN '{}' AND '{}' GROUP BY timestamp".format(databasename, start_date, end_date))

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

def return_target_device_data(start_date):
    db_config = {
        "host": "127.0.0.1",
        "user": "root",
        "password": "root",
        "database": "simulationDB"
    
    }

    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        #Qquert som hämtar allt från targetdevice från dagen innan
        cursor.execute("SELECT timestamp, average_load, total_load, instances FROM target_device WHERE DATE(timestamp) >= %s", (start_date,))
      #  cursor.execute("SELECT timestamp, average_load, total_load, instances FROM target_device")
                       
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

def return_target_service_data():
    db_config = {
        "host": "127.0.0.1",
        "user": "root",
        "password": "root",
        "database": "simulationDB"
    
    }

    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        #Query som hämtar all taget servic data
        cursor.execute("SELECT * FROM target_service")
                       
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
        end_date = request.json.get('end_date', None)
        databasename = request.json.get('databasename', None)

        if start_date and end_date is not None:
            data = fetch_and_return_data(databasename,start_date,end_date)
            return make_response(jsonify(data), 200)
        elif start_date is not None:
            end_date = start_date+timedelta(days=1)
            data = fetch_and_return_data(databasename,start_date,end_date)
            return make_response(jsonify(data), 200)
        
        previous_day = request.json.get('autoscaler', None)
        if previous_day is not None:
            target_data = return_target_device_data(previous_day)
            return make_response(jsonify(target_data), 200)
        
        target_service_data = request.json.get('target_service_data', None)
        if target_service_data is not None:
            print("Hej")
            historical_data = return_target_service_data()
            return make_response(jsonify(historical_data), 200)
    
    def post(self):
        total_load = request.json.get('total_load', None)
        average_load = request.json.get('average_load', None)
        instances_scaled = request.json.get('instances_scaled', None)
        timestamp = request.json.get('time', None)
        if total_load is not None:
            add_target_load(average_load, total_load, instances_scaled, timestamp)
        applied_load = request.json.get('applied_load', None)
        experienced_load = request.json.get('experienced_load', None)
        current_time = request.json.get('current_time', None)
        instances = request.json.get('instances', None)
        if applied_load is not None:
            add_target_service_load(applied_load, experienced_load, current_time, instances)
        
api.add_resource(DatabaseService, "/databaseservice") 

if __name__ == "__main__":
    app.run(debug=False, host='0.0.0.0',use_reloader=False) #Startar flask server för DatabaseService 
