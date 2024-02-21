import requests

QuerytoolBASE = "http://127.0.0.1:5000/"
LoadGenBASE = "http://127.0.0.1:8002/"

#response = requests.post(BASE+"Workload/45") #Skickar en post request
#print(response.json())

response = requests.get(LoadGenBASE+"loadgenerator/1998-05-02/10s") #Skickar en GET request
#print(response.json())

#response = requests.get(QuerytoolBASE+"databaseservice/1998-05-01/60s")
#print(response.json())