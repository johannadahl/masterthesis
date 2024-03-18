import pandas as pd
import time
from flask import Flask,jsonify,make_response,request
from flask_restful import Api, Resource,request
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
                time.sleep(5) # detta kanske är fusk, borde vara en inparameter
            except ValueError as e:
                return {'error': str(e)}, 400
            
def return_all_simulation_data(data_result, resample_frequency):
    if data_result is not None:
        column_names = ["time", "method_count"]
        df = pd.DataFrame(data_result, columns=column_names)
        df['time'] = pd.to_datetime(df['time'], format='%a, %d %b %Y %H:%M:%S GMT')
        df['method_count'] = df['method_count'].astype(int)

        df_frequency = df.set_index('time').resample(resample_frequency).sum()
        print("First 15 values in the resampled DataFrame:", df_frequency.head())
        return df_frequency
            

def start_load(start_date,end_date,freq):
    databasename = "allworldcup98"
    response = requests.get(QuerytoolBASE+"databaseservice",json={"start_date": start_date,"end_date":end_date, "databasename": databasename})
    data_result = response.json()
    data = return_all_simulation_data(data_result, freq)
    return data

class LoadGenerator(Resource):

    def get(self):
        start_date = request.args.get('start_date', None)
        end_date = request.args.get('end_date', None)
        resample_frequency = request.args.get('resample_frequency', None)
        data = start_load(start_date,end_date, resample_frequency) 
        payload = data.reset_index().to_json(orient='records')
        return payload

api.add_resource(LoadGenerator, "/load_generator") 

if __name__ == "__main__":
    app.run(debug=False,port = 8009, host='0.0.0.0',use_reloader=False) #Startar flask server för Load Generator 


