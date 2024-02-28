
import matplotlib.pyplot as plt
import pandas as pd
import requests
from flask import request
import datetime

TargetServiceBASE = "http://127.0.0.1:8003/"
QuerytoolBASE = "http://127.0.0.1:5000/"

def plot_workload(data_result):
    column_names = ["time", "method_count"]
    df = pd.DataFrame(data_result, columns=column_names)
    df = df.set_index('time')
    df['method_count'] = df['method_count'].astype(int)
    plt.plot(df.index, df['method_count'])
    plt.show()

def check_current_day():
    response = requests.get(TargetServiceBASE+"targetservice",json = {"time_request": True}) #Skickar en request om att starta en load
    date = response.json()
    return date

def return_previous_day(current_day):
    current_day = datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
    day_before = current_day - datetime.timedelta(days=1)
    day_before_str = day_before.strftime("%Y-%m-%d")
    return day_before_str
  
#Körs en dång per dag? Sätts igång i början av dagen och sedan predictar den för dagen som är??
if __name__ == "__main__":
    date = check_current_day()
    previous_day = return_previous_day(date)

    #Hämtar data från tidigare dag
    response = requests.get(QuerytoolBASE+"databaseservice",json={"autoscaler": previous_day})
    data_result = response.json()
    print(date)
    print(previous_day)
    print(data_result)