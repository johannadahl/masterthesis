from flask import Flask,request
from flask_restful import Api, Resource
import requests


app = Flask(__name__)
api = Api(app)
TargetServiceBASE = "http://127.0.0.1:8003/"
QuerytoolBASE = "http://127.0.0.1:5000/"


#load recorder class 
class LoadRecorder(Resource):

    def post(self):
        total_load = request.json.get('total_load', None)
        average_load = request.json.get('average_load', None)
        instances_scaled = request.json.get('instances_scaled', None)
        print(total_load,average_load,instances_scaled)
        requests.post(QuerytoolBASE + "databaseservice", json={"total_load": total_load, "average_load": average_load,"instances_scaled": instances_scaled})
        return {'status': 'success'}

api.add_resource(LoadRecorder, "/loadrecorder") 

if __name__ == "__main__":
    app.run(debug=True,use_reloader=False, port=8008, host='0.0.0.0')
