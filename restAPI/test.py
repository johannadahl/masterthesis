import requests

BASE = "http://127.0.0.1:5000/"

response = requests.get(BASE+"GetNames/Johanna") #Skickar en GET request
print(response.json())

response = requests.post(BASE+"Workload/45") #Skickar en post request
print(response.json())