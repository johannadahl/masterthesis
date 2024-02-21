#Skelett till Target Service
from flask import Flask
from flask_restful import Api, Resource
import requests

app = Flask(__name__)
api = Api(app)

def preform_cpu_usage():
    ##Här lägger vi in en gigatisk for-loop tex
    print("For loop")

def get_workload():
    #Hämta workload genom att skicka GET request till Load Generator
    print("Tex Current workload = 3")

class TargetService(Resource):
    def post(self, workload):
        print(workload)

api.add_resource(TargetService, "/targetservice/<int:workload>") 

    
if __name__ == "__main__":
    app.run(debug=True,port=8003) #Startar flask server för DatabaseService 
    #Skicka till eller hämta från load recorder

