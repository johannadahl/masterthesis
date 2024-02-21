import sys
import pandas as pd
import time
from flask import Flask
from flask_restful import Api, Resource
from databaseservice.querytool import fetch_and_return_data

app = Flask(__name__)
api = Api(app)

def process_data(data_result, resample_frequency):

    if data_result is not None:
        column_names = ["time", "method_count"]
        df = pd.DataFrame(data_result, columns=column_names)

        # Detta är för per 10:e sekund! ska göras om till en egen function sen 
        df['time'] = pd.to_datetime(df['time'])
        df_10_seconds = df.set_index('time').resample(resample_frequency).sum()
        print("First 15 values in the resampled DataFrame:", df_10_seconds.head())

        for index, row in df_10_seconds.iterrows():
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

