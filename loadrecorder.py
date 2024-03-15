from flask import Flask,request
from flask_restful import Api, Resource
import requests


app = Flask(__name__)
api = Api(app)
TargetServiceBASE = "http://127.0.0.1:8003/"
QuerytoolBASE = "http://127.0.0.1:5000/"


# Load recorder class 
class LoadRecorder(Resource):

    def post(self):
        ##Dehär är den gamla targetservicen
        total_load = request.json.get('total_load', None)
        average_load = request.json.get('average_load', None)
        instances_scaled = request.json.get('instances_scaled', None)
        timestamp = request.json.get('time', None)
        
        if total_load is not None:
            requests.post(QuerytoolBASE + "databaseservice", 
                          json={"total_load": total_load, 
                                "average_load": average_load,
                                "instances_scaled": instances_scaled, 
                                "time": timestamp}
                                )
            return {'status': 'success'} 
        
        ##Nya versionen
        applied_load = request.json.get('applied_load', None)
        experienced_load = request.json.get('experienced_load', None)
        current_time = request.json.get('current_time', None)
        instances = request.json.get('instances', None)
        if applied_load is not None:
            requests.post(QuerytoolBASE + "databaseservice", 
                      json={"applied_load": applied_load,
                            "experienced_load": experienced_load,
                            "current_time": current_time,
                            "instances": instances}
                            )
            return {'status': 'success'} 
               

api.add_resource(LoadRecorder, "/loadrecorder") 

if __name__ == "__main__":
    app.run(debug=False,use_reloader=False, port=8008, host='0.0.0.0')
