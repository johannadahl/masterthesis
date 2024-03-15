import pandas as pd
import numpy as np
import requests
import xgboost as xgb
from sklearn.metrics import mean_squared_error

## Skapar en abstract för en prediction model 

class Predictor():
    def __init__(self):
        self.model = None

    def import_historical_dataset(self):
        QuerytoolBASE = "http://127.0.0.1:5000/"
        response = requests.get(QuerytoolBASE+"databaseservice",json={"target_service_data": "True"})
        data_result = response.json()
        historical_df = pd.DataFrame(data_result, columns=["timestamp", "applied_load", "experienced_load", "instances"])
        return historical_df
    
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

    def generate_future_values(self, df):
        end_date = df.index.max()
        # Create future dataframe
        future = pd.date_range(end_date,'1995-08-05 00:00:00', freq='1h')
        future_df = pd.DataFrame(index=future)
        future_df['isFuture'] = True
        df['isFuture'] = False
        df_and_future = pd.concat([df, future_df])
        future_df = df_and_future.query('isFuture').copy()
        return future_df, df_and_future



    def predict(self, prediction_model, X_test,y_test):

        pass