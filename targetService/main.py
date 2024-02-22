#Skelett till Target Service
from flask import Flask,request
from flask_restful import Api, Resource
import requests
import threading



app = Flask(__name__)
api = Api(app)
LoadGenBASE = "http://loadgenerator:8002/"

def preform_cpu_usage():
    ##Här lägger vi in en gigatisk for-loop tex
    print("For loop")

class TargetService(Resource):

    def __init__(self, workload=0):
        self.workload = workload

    def post(self):
        workload = request.json.get('workload', None)
        if workload is not None:
            print(workload)
            self.workload = workload  # försöker koppla workload till en specifik device, går sådär:(/)
            return {'message': 'Current workload updated'}, 200
        else:
            return {'error': 'No workload'}, 400


api.add_resource(TargetService, "/targetservice") 

def start_flask():
    app.run(debug=True, port=8003,use_reloader=False, host='0.0.0.0') #Startar flask server för TargetService på en annan tråd! 

if __name__ == "__main__":


    flask_thread = threading.Thread(target=start_flask) #Flaskservern måste köras på en egen tråd! annars kan man inte köra annan kod samtidigt 
    flask_thread.start()

    target_service = TargetService(0)
    print("Instansierar targetservice", target_service.workload)
    response = requests.get(LoadGenBASE+"loadgenerator/1998-05-02/10s") #skickar en request om att starta en load


