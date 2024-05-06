
from predictor import Predictor
import pandas as pd
import numpy as np, pandas as pd
import matplotlib.pyplot as plt

import warnings
warnings.filterwarnings("ignore")
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.tsa.stattools import adfuller
#from pandas import datetime
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX
from sklearn.metrics import mean_squared_error
from math import sqrt
import pandas as pd
from matplotlib import pyplot
from sklearn.metrics import mean_squared_error
from math import sqrt
import pmdarima as pm



class ARIMAPredictor(Predictor):

    def __init__(self):
        self.model = None
        self.order = None

    def create_mask_train_test_split(self,df):
        msk = df.index < (df.index[-1] - pd.Timedelta(hours=180))
        df_train = df[msk].copy()
        df_test = df[~msk].copy()

        result = adfuller(df['total_load'])
        print('ADF Statistic: %f' % result[0])
        print('p-value: %f' % result[1]) # if p-value is > 0.05 --> differenciate again!!!
        print('Critical Values:')

        for key, value in result[4].items():
            print('\t%s: %.3f' % (key, value))
        

        return df_train, df_test
    
    def differencing(self,df):

        plt.rcParams.update({'figure.figsize':(9,7), 'figure.dpi':120})
        
        # Original Series
        fig, (ax1, ax2, ax3) = plt.subplots(3)
        ax1.plot(df); ax1.set_title('Worldcup'); ax1.axes.xaxis.set_visible(False)
        # FÖRSTA Differencing
        ax2.plot(df.diff()); ax2.set_title('1st Order Differencing'); ax2.axes.xaxis.set_visible(False)
        # ANDRA Differencing
        ax3.plot(df.diff().diff()); ax3.set_title('2nd Order Differencing')
        plt.show()

        # Titta på vart kurvan stationeras, samt vilken som har minst noice. Detta blir d-värdet!!!

    def train_model(self, df):
        """
        Tränar en SARIMA model på all historisk data som finns
        Tar var 60:de tal (tar för lång tid annars)

        Ändra p,d,q för olika resultat
        """

        sampled_df = df.iloc[::60]

# 0.99 innebär att inprincip all data blir träningsdata
#Gör sifftan lägre om de tar för långt tid
        split_index = int(0.30 * len(sampled_df))
        train_df = sampled_df.iloc[:split_index]
        test_df = sampled_df.iloc[split_index:]
        #df = df.resample('H').mean()
        df = df.iloc[::60]

        split_index = int(0.6 * len(df))
        train_df = df.iloc[:split_index]
        test_df = df.iloc[split_index:]
        X_train = train_df['applied_load']

        self.index = df.index
        print(self.index)
        self.order = (7,0,2) # order from autoarima  (cna be found in PACF and residuals plots as well)
        self.seasonal_order = (7,0,2,24) # seasonal order from autoarima (can be found in PACF and residuals plots as well)
        model = SARIMAX(X_train, order=self.order, seasonal_order=self.seasonal_order)
        self.model = model.fit()

        print("Final ARIMA model summary:")
        print(self.model.summary())

        return self.model
    
    def generate_forecast(self):
        forecast_periods = 200 
        forecast = self.model.get_forecast(steps=forecast_periods)
        forecast_mean = forecast.predicted_mean
        forecast_ci = forecast.conf_int()

        return forecast,forecast_mean,forecast_ci
    
    def generate_predictions(self,start_date,end_date):
        if self.model is None:
            raise ValueError("Model has not been trained yet.")
        predictions = self.model.predict(start=start_date, end=end_date, dynamic=False, information_set='predicted', signal_only=False)
        return predictions
    
    def validate_model(self, df):
        
        split_index = int(0.66 * len(df))
        train = df.iloc[:split_index]['applied_load']
        test = df.iloc[split_index:]['applied_load']

        history = [x for x in train]
        predictions = []

        #walk forward (istället för att göra en prediction på hela datan) obs tar TID
        for t in range(len(test)):
            model = ARIMA(history, order=self.order)
            model_fit = model.fit()
            output = model_fit.forecast()
            yhat = output[0]
            predictions.append(yhat)
            obs = test[t]
            history.append(obs)
            print('predicted=%f, expected=%f' % (yhat, obs))

        rmse = sqrt(mean_squared_error(test, predictions))
        print('Test RMSE: %.3f' % rmse)
    
    def evaluation(self, df_test, predictions):
        rmse = sqrt(mean_squared_error(df_test, predictions))
        print('Test RMSE: %.3f' % rmse)

        #plotting the data
        pyplot.plot(df_test, label='Actual')
        pyplot.plot(predictions, color='red', label='Predicted')
        pyplot.legend()
        pyplot.grid()
        pyplot.show()