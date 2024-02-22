from flask import Flask
from flask_restful import Api, Resource
import requests

#### omgjord!! skelett 

app = Flask(__name__)
api = Api(app)

def get_cpu_usage():
    target_url = "http://targetservice:5000/cpu_usage"  # kanske måste ha en docker compose fil för detta + ändra endpoint
    response = requests.get(target_url)

    cpu_info = response.json()
    print (cpu_info)
    return cpu_info


#load recorder class 
class LoadRecorder(Resource):
    def post(self, workload):
        print(workload)

        # get CPU info from target container 
        cpu_info = get_cpu_usage()
        print(cpu_info)   # lägga i databas istälet för att printa 

        return {'status': 'success'}

api.add_resource(LoadRecorder, "/loadrecorder/<int:workload>") 

if __name__ == "__main__":
    app.run(debug=True, port=8008, host='0.0.0.0')
