import sys
import pandas as pd
import time
import requests
from flask import Flask
from flask_restful import Api, Resource
from databaseservice.queryTool import fetch_and_return_data

app = Flask(__name__)
api = Api(app)

def process_data(data_result, resample_frequency):
    if data_result is not None:
        for index, row in data_result.iterrows():
            print(f"Method count for {index}: {row['method_count']}")
            time.sleep(10) # detta kanske är fusk, borde vara en inparameter

def start_load(date,freq):
    data_result = fetch_and_return_data(date, freq)
    process_data(data_result, freq)
class LoadGenerator(Resource):

    def get(self,start_date,resample_frequency): ##Override! This is what happens when we send a get request to the Load generator (starts a load)
        start_load(start_date,resample_frequency) 

api.add_resource(LoadGenerator, "/generate_load/<string:start_date>/<string:resample_frequency>") 

if __name__ == "__main__":
    app.run(debug=True) #Startar flask server för Load Generator 

#Har kommenterat ut detta sålänge!
#    if len(sys.argv) != 3:
 #       print("MÅSTE SKRIVAS SOM: python loadGenerator.py start_date resample_frequency")
 #       sys.exit(1)

 #   start_date = sys.argv[1]
  #  resample_frequency = sys.argv[2]

  #  from databaseservice.queryTool import fetch_and_return_data

  #  data_result = fetch_and_return_data(start_date, resample_frequency)

  #  process_data(data_result, resample_frequency)

