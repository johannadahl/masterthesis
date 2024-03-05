
#En början på prediktionsalgoritm som anänder Support Vector Regression

import matplotlib.pyplot as plt
import pandas as pd
import requests
from flask import request
import datetime
from sklearn.svm import SVR
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
import numpy as np
from numpy import mean, std

TargetServiceBASE = "http://127.0.0.1:8003/"
QuerytoolBASE = "http://127.0.0.1:5000/"

##Onödiga funktioner, ligger kvar sålänge
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
  
#Prediction model - Support Vector Machine
def prepare_data_for_training(historical_data):
    X = pd.to_datetime(historical_data['timestamp']).astype(int).values.reshape(-1, 1)
    y = historical_data['total_load'].values
    return X, y

def delete_outliers(historical_df):
    data_mean, data_std = mean(historical_df["total_load"]), std(historical_df["total_load"])
    cut_off = data_std * 1 #Räknas som outliers om de är mer än 2 standard deviations från medelvärdet. 
    lower, upper = data_mean - cut_off, data_mean + cut_off

    outliers = [x for x in historical_df["total_load"] if x < lower or x > upper]
    print('Identified outliers: %d' % len(outliers))
    ...
    outliers_removed = [x for x in historical_df["total_load"] if x > lower and x < upper]
    print(len(outliers_removed))
    historical_df_outliers_removed = historical_df[(historical_df["total_load"] > lower) & (historical_df["total_load"] < upper)]
    return historical_df_outliers_removed


def train_svm_model_on_historical_data(historical_data):
    X, y = prepare_data_for_training(historical_data)
   # model = make_pipeline(StandardScaler(), SVR(C=1.0, epsilon=0.2))
    svr = SVR().fit(X, y)
    return svr

def predict_workload(model, X):
    predicted_workload = model.predict(X)
    return predicted_workload

def return_target_data():
    #Hämtar data från target_device databasen
    response = requests.get(QuerytoolBASE+"databaseservice",json={"autoscaler": "1998-05-02"})
    data_result = response.json()
    historical_df = pd.DataFrame(data_result, columns=['timestamp', 'average_load', 'total_load', 'instances'])
   # historical_df = pd.DataFrame(data_result, columns=['timestamp', 'requests'])
    return historical_df
    
#Tränas på all data som finns samlad om target device so far
if __name__ == "__main__":
    #date = check_current_day()
    #previous_day = return_previous_day(date)
    historical_df = return_target_data()

    # Convert timestamp column to datetime (from mysql time)
    historical_df['timestamp'] = pd.to_datetime(historical_df['timestamp']) 
    historical_df = delete_outliers(historical_df)
    svm_model = train_svm_model_on_historical_data(historical_df)

    last_date = historical_df['timestamp'].max()
    first_date = historical_df['timestamp'].min()
    next_day = last_date + pd.DateOffset(days=1)

    #Prepare next day timestamps, starting from the beginning of the next day 
    next_day_timestamps = pd.date_range(start=next_day.replace(hour=0, minute=0, second=0), end=next_day, freq='T')
    all_days= pd.date_range(start=first_date.replace(hour=0, minute=0, second=0), end=next_day+ pd.DateOffset(days=1), freq='T')

    predicted_workload = predict_workload(svm_model, all_days.astype(int).values.reshape(-1, 1)) #Fett tveksam på detta
    print("Predicted:",predicted_workload )
    print(next_day_timestamps)
    
    # Plot the historical data first as a reference
    plt.plot(historical_df['timestamp'], historical_df['total_load'], label='Historical Data')

    # Plot the predicted workload for the next day after the historical one
    plt.plot(all_days, predicted_workload, label='Predicted Workload')

    plt.xlabel('Timestamp')
    plt.ylabel('Target Device Total Load')
    plt.title('Predicted Workload for Upcoming Day')
    plt.legend()
    plt.show()