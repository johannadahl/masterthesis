import pandas as pd
import time
from flask import Flask,jsonify,make_response
from flask_restful import Api, Resource
import requests

app = Flask(__name__)
api = Api(app)
QuerytoolBASE = "http://127.0.0.1:5000/"
TargetServiceBASE = "http://127.0.0.1:8003/"

def process_data(data_result, resample_frequency):

    if data_result is not None:
        column_names = ["time", "method_count"]
        df = pd.DataFrame(data_result, columns=column_names)
        df['time'] = pd.to_datetime(df['time'])
        df['method_count'] = df['method_count'].astype(int)

        df_frequency = df.set_index('time').resample(resample_frequency).sum()

        print("First 15 values in the resampled DataFrame:", df_frequency.head())
        for index, row in df_frequency.iterrows():

            print(f"Method count for {index}: {row['method_count']}")
            method_count = int(row['method_count'])
            timestamp = index
            try:
                requests.post(TargetServiceBASE + "targetservice", json={"workload": method_count, "time": str(timestamp)})
                time.sleep(1) # detta kanske är fusk, borde vara en inparameter
            except ValueError as e:
                return {'error': str(e)}, 400
            

def start_load(date,freq):
    response = requests.get(QuerytoolBASE+"databaseservice",json={"start_date": date})
    data_result = response.json()
    process_data(data_result, freq)

class LoadGenerator(Resource):

    def get(self,start_date,resample_frequency): ##Override! This is what happens when we send a get request to the Load generator (starts a load)
        start_load(start_date,resample_frequency) 
        return {"message": "Load started"}, 200

api.add_resource(LoadGenerator, "/loadgenerator/<string:start_date>/<string:resample_frequency>") 

if __name__ == "__main__":
    app.run(debug=True,port = 8002, host='0.0.0.0') #Startar flask server för Load Generator 


