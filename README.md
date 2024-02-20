### Master Thesis Project
##

### Load Generator
The Load Generator simulates workload in terms of requests to a server per time unit. It utilizes data from the WorldCup98 database.

First, initiate a Flask App to listen for requests:


````bash
python3 restAPI/flaskapp.py
````
Then, run the Load Generator using:

````bash
python3 database/loadGenerator.py start_date resample_frequency
````

Example:

````bash
python3 database/loadGenerator.py 1998-05 5s
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
