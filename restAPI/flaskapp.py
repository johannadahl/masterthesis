#The script starts a Flask Server and a Rest API

from flask import Flask
from flask_restful import Api, Resource

app = Flask(__name__)
api = Api(app)

names = {"Elsa": {"age": 25, "gender": "girl"},
         "Johanna": {"age": 26, "gender": "girl"}}

class GetNames(Resource):
    def get(self,name): ##Override! This is what happens when we send a get request to the HelloWorld class
        return names[name]

class Workload(Resource):
    def post(self,requests): ##Override! This is what happens when we send a get request to the HelloWorld class
        return requests
    
api.add_resource(GetNames, "/GetNames/<string:name>") #How can you find/access helloworld class. 
api.add_resource(Workload, "/Workload/<int:requests>") 

if __name__ == "__main__":
    app.run(debug=True) #only in development mode