### Master Thesis Project
##

### Target Device

The Target Device sends a get request to the load generator to start a simulated load. Calculates available instances to met the load. Simulates a real device. 
To be able to run this script make sure ALL THREE flask servers for the other modules are running. Then, initiate a target device for a wanted starting date and request frequency using:

````bash
python3 targetservice/main.py -start_date --resample_frequency
````

### Database service
Preforms queries/interaction with the MySql database. Listens to GET requests from Load generator and Autoscaler and POST requests from Load recorder. 
slart flask server with: 

````bash
python3 databaseservice/querytool.py
````

### Load Generator
The Load Generator simulates workload in terms of requests to a server per time unit. By default it utilizes data from the WorldCup98 database.
Listens for GET requests that initiates a load, after that, workload is forced to the target device.

Start the Load Generator flask server using:

````bash
python3 loadgenerator.py
````


### Load recorder
Records load data from target service. Listens to POST requests from Target Device when it is running and reports to the database service.  
Start Flask server
````bash
python3 loadrecorder.py
````



### Add data to the MySQL database 
Make sure Elsa-mysql container is running on the administrator server.

Take a look what addjsondata.py is hardcoded to, currently it connects to simulationDB (change depending on your preference).

````bash
administrator@e24:~/masterthesis$ python3 database/addjsondata.py < <(python3 /home/administrator/cbsa_tools/view.py --dataset WORLDCUP98 --input /home/administrator/cbsa_tools/worldcup98.zip --start [time] --duration [in hours] --format json)
````
For example: 
````bash
python3 database/addjsondata.py < <(python3 /home/administrator/cbsa_tools/view.py --dataset WORLDCUP98 --input /home/administrator/cbsa_tools/worldcup98.zip --start 1998-06-22T21:00:00 --duration 3h --format json)
````
