#Skelett till Target Service
from flask import Flask,request
from flask_restful import Api, Resource
import requests
import threading



app = Flask(__name__)
api = Api(app)
LoadGenBASE = "http://127.0.0.1:8002/"
LoadRecBASE = "http://127.0.0.1:8008/"

def load_calculator(requests):
    print("Räkna ut hur mycket kärnor det behövs baserat på requests per timeintervall")
    current_load = requests/100
    return current_load

class TargetService(Resource):

    def __init__(self, total_load = 0, instances_scaled = 1):
        self.total_load = total_load
        self.average_load = total_load/instances_scaled ##Kanske inte ska vara heltalsdivision men de är det så länge
        self.instances_scaled = instances_scaled
        self.threshold = 50 #Tröskel! vet inte vad som är rimligt
        self.timestamp = None

    def post(self):
        print("targetservice current values BEFORE", target_service.total_load, target_service.average_load,target_service.instances_scaled)
        workload = request.json.get('workload', None)
        current_time = request.json.get('time', None)
        if workload is not None: 
            print(workload)
            target_service.total_load = workload
            target_service.timestamp = current_time
            target_service.update_load()
            target_service.instances_calculator()
            target_service.update_load() #This is to get the new average_load load after instances is updated!
            print("targetservice current values", target_service.total_load, target_service.average_load,target_service.instances_scaled)

            requests.post(LoadRecBASE + "loadrecorder", json={"total_load": target_service.total_load, "average_load": target_service.average_load,"instances_scaled": target_service.instances_scaled, "time": target_service.timestamp})

            return {'message': 'Current workload updated'}, 200
        else:
            return {'error': 'No workload'}, 400
        
    def instances_calculator(self):
        scaling_needed = True
        while scaling_needed:
            if self.average_load > self.threshold:
                self.instances_scaled +=1
                self.update_load()
                if self.average_load < self.threshold:
                    scaling_needed = False
            elif self.instances_scaled > 1 and self.total_load/(self.instances_scaled-1) < self.threshold: 
                print(self.instances_scaled,self.average_load,self.threshold)
                self.instances_scaled -=1
                self.update_load()
                if self.instances_scaled > 1 and self.total_load/(self.instances_scaled-1) > self.threshold:
                    scaling_needed = False
            else:
                scaling_needed = False
                print("Scaling wasnt needed.")
            
    
    def update_load(self):
        self.average_load = self.total_load/self.instances_scaled


api.add_resource(TargetService, "/targetservice") 

def start_flask():
    app.run(debug=True, port=8003,use_reloader=False, host='0.0.0.0') #Startar flask server för TargetService på en annan tråd! 

def create_target_service_with_workload(workload):
        target_service = TargetService(workload, 1)  
        print("Instantiating target service with workload:", target_service.total_load)
        return target_service

if __name__ == "__main__":

    flask_thread = threading.Thread(target=start_flask) #Flaskservern måste köras på en egen tråd! annars kan man inte köra annan kod samtidigt 
    flask_thread.start()
    global target_service
    target_service = create_target_service_with_workload(0)
    response = requests.get(LoadGenBASE+"loadgenerator/1998-05-02/10s") #Skickar en request om att starta en load


