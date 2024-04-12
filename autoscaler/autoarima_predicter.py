
from predictor import Predictor
import pandas as pd
import numpy as np, pandas as pd
import matplotlib.pyplot as plt
from numpy import mean
from numpy import std
import pmdarima as pm

import warnings
warnings.filterwarnings("ignore")
from pmdarima import auto_arima
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.tsa.stattools import adfuller
#from pandas import datetime
from statsmodels.tsa.arima.model import ARIMA
from sklearn.metrics import mean_squared_error
from math import sqrt
import pandas as pd
from matplotlib import pyplot


class ARIMAPredictor(Predictor):

    def __init__(self):
        self.model = None

    def create_df(self,df):
        df = df.copy()
        df['hour'] = df.index.hour
        return df
    
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

    def apply_autoarima(self,df_train):
        auto_arima = pm.auto_arima(df_train, stepwise = False, seasonal = False)
        auto_arima


    def train_model(self,df):

        X = df['applied_load'].values
        size = int(len(X) * 0.66)
        df_train, df_test = X[0:size], X[size:len(X)]
        history = [x for x in df_train]
        order_nasa = (3, 0, 0)

        for t in range(len(df_test)):
            model = ARIMA(history, order=order_nasa)
            model_fit = model.fit()
            obs = df_test[t]
            history.append(obs)

        self.model = model_fit
       
        
    

    def generate_predictions(self, df_test):
       
        #df = self.generate_X_values(start_date, end_date)
        X = df_test['total_load'].values
        predictions = []
        
        history = [x for x in X]  # ändrade detta för att lättare träna kanske tar mindre tid?
        
        for x in X:
            output = self.model.forecast(steps=1)  
            yhat = output[0]
            predictions.append(yhat)
            # Update
            history.append(yhat)

        return predictions

    def evaluation(self, df_test, predictions):
        rmse = sqrt(mean_squared_error(df_test, predictions))
        print('Test RMSE: %.3f' % rmse)

        #plotting the data
        pyplot.plot(df_test, label='Actual')
        pyplot.plot(predictions, color='red', label='Predicted')
        pyplot.legend()
        pyplot.grid()
        pyplot.show()