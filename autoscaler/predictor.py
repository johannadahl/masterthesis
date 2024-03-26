import pandas as pd
import numpy as np
import requests
import xgboost as xgb
from sklearn.metrics import mean_squared_error
from datetime import timedelta

class Predictor():
    """""
    General Predictor class. Upper Class that includes all common function to all inner predictor classes with varying prediction models.
      
    """""
    def __init__(self):
        self.model = None

    def import_historical_dataset(self):
        QuerytoolBASE = "http://127.0.0.1:5000/"
        response = requests.get(QuerytoolBASE+"databaseservice",json={"target_service_data": "True"})
        data_result = response.json()
        if data_result != []:
            historical_df = pd.DataFrame(data_result, columns=["timestamp", "applied_load", "experienced_load", "instances"])
            return historical_df
        else:
            return None
    
    def preprocess_data(self,df):
        df['timestamp'] = pd.to_datetime(df['timestamp'],format='%a, %d %b %Y %H:%M:%S GMT') 
        df['applied_load'] = df['applied_load'].astype(float)
        df = df.set_index("timestamp")
        df = df.sort_index()

        df = df.drop(columns=[ 'experienced_load', 'instances']) # Droppar dessa för nu! Kanske behållas som features sen?
        return df   

    def remove_outliers(self,df):
        Q1 = df['applied_load'].quantile(0.35)
        Q3 = df['applied_load'].quantile(0.90)

        IQR = Q3 - Q1

        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR

        df_filtered = df[(df['applied_load'] >= lower_bound) & (df['applied_load'] <= upper_bound)]
        return df_filtered

    def generate_X_values(self, start_date, end_date):
        future = pd.date_range(start_date, end_date, freq='1min')
        future_df = pd.DataFrame(index=future)
        future_df = future_df.iloc[:-1]  # Exclude the last timestamp
        return future_df
    
    def predict_load(self, reg, df):
        FEATURES = ['hour', 'dayofweek',
                'lag1','lag2','lag3']
        
        df['pred'] = reg.predict(df[FEATURES])
        return df
    
    ## MAPE - gives the avarage percent off what our prediction is from the ground truth.
    def mean_absolute_percentage_error(self, y_true, y_pred): 
        y_true, y_pred = np.array(y_true), np.array(y_pred)
        return np.mean(np.abs((y_true - y_pred) / y_true)) * 100