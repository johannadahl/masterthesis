
from predictor import Predictor
import pandas as pd
import numpy as np, pandas as pd
import matplotlib.pyplot as plt
from numpy import mean
from numpy import std
import pmdarima as pm
from sklearn.model_selection import TimeSeriesSplit
import warnings
warnings.filterwarnings("ignore")
from pmdarima import auto_arima
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



    def train_model_w(self, df):
        self.order = (1, 0, 0)  #default
        self.model = None #(walk forward validation)

    def generate_predictions_w(self, df):
        if self.model is None:
            raise ValueError("Model has not been trained yet.")
        
        predictions = []

        for i in range(len(df)):
            
            current_timestamp = df.index[i] #timestamp och load
            current_load = df.iloc[i]['applied_load']
            
            
            if self.model is None: #träna modellen innan den har nåtts av någon typ av data 
                self.model = ARIMA(current_load, order=self.order)
                self.model = self.model.fit()
            else:
                self.model = self.model.append(current_load)
                self.model = self.model.fit()

            
            forecast = self.model.forecast(steps=1) #forecastar ett steg i taget
            
            predictions.append(forecast[0])
        
        predictions = np.array(predictions)
        
        return predictions


    def apply_autoarima(self,df_train):
        auto_arima = pm.auto_arima(df_train, stepwise = False, seasonal = False)
        auto_arima

        
        
    def train_model_s(self, df):

        split_index = int(0.5 * len(df))
        train_df = df.iloc[:split_index]
        test_df = df.iloc[split_index:]
        X_train = train_df['applied_load']
        self.order = (2, 0, 1) 
        self.seasonal_order = (0,1,1,1440)
        
        #self.model = SARIMAX(X_train, order=self.order, seasonal_order=self.seasonal_order)
        #self.model = self.model.fit()

        self.model = auto_arima(X_train, seasonal=False)
        self.model.fit(X_train)
        print("Final SARIMA model summary:")
        print(self.model.summary())
        return self.model

    def generate_predictions_s(self, start_date, end_date):
        if self.model is None:
            raise ValueError("Model has not been trained yet.")
        predictions = []
        for date in pd.date_range(start=start_date, end=end_date, freq='T'):
            current_load = df.loc[date]['applied_load']
            self.model = self.model.append(current_load)
            self.model = self.model.fit()
            forecast = self.model.forecast(steps=1)
            predictions.append(forecast[0])
        predictions = np.array(predictions)
        return predictions

    def train_model(self, df):

        #df = df.resample('H').mean()
        df = df.iloc[::60]

        split_index = int(0.6 * len(df))
        train_df = df.iloc[:split_index]
        test_df = df.iloc[split_index:]
        X_train = train_df['applied_load']

        #X = df['applied_load']
    
        self.index = df.index
        print(self.index)
        self.order = (7,0,2) # order from autoarima  (cna be found in PACF and residuals plots as well)
        self.seasonal_order = (7,0,2,24) # seasonal order from autoarima (can be found in PACF and residuals plots as well)
        self.model = SARIMAX(X_train, order=self.order, seasonal_order=self.seasonal_order)
        #self.model = ARIMA(X_train, order=self.order) 
        """
        De som behövdes läggas till här är en index log, så att den fattar hur den ska hantera framtida prediktioner. 
        Den lägger alltså till timestamps för hela den råa NASA datan, även om den bara tränar på halva.
        Annars hittar den inte när man önskar predictions för index som den inte har tränat på (tex on vill ha predictions mellan 25-30 julli). 
        
        Detta kanske vi kan kika på snyggare lösning

        """
        #end_date = pd.to_datetime('1995-07-30 00:00:00') #End date in nasa_full dataset
        #extended_index = pd.date_range(start=df.index.min(), end=end_date, freq='T')

        #df = df.reindex(extended_index)
        #X = df['applied_load']
        #print("mitt i träningen",df)
        #self.index = df.index
        #print(self.index)

        #self.order = (3, 0, 2)
        #self.model = ARIMA(X, order=self.order)

        self.model = self.model.fit()

        print("Final ARIMA model summary:")
        print(self.model.summary())

        return self.model
    

    def generate_predictions(self, start_date, end_date):
        if self.model is None:
            raise ValueError("Model has not been trained yet.")

        predictions = self.model.predict(start=start_date, end=end_date, typ ="levels")
        #predictions = forecast.p redicted_mean

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

    def date_to_index(self, date):

            return date   
    
    def generate_predictions_old(self, start_date, end_date):
        if self.model is None:
            raise ValueError("Model has not been trained yet.")

        predictions = []
        current_date = start_date
        while current_date <= end_date:
            train_end_date = current_date
            #make the 
            train_start_date = train_end_date - pd.Timedelta(days=1)  #detta är numera satt som 1 dag 
            train_data = df.loc[:train_end_date]

            X_train = train_data['applied_load']
            self.model = ARIMA(X_train, order=self.order)
            self.model = self.model.fit()

            forecast = self.model.forecast(steps=1)

            current_date += pd.Timedelta(days=1)

            predictions.append(forecast[0])

        return predictions
    


    
    def generate_predictions3(self, start_date, end_date):

        if self.model is None:
            raise ValueError("Model has not been trained yet.")
        date_range = pd.date_range(start=start_date, end=end_date, freq='1T')
        
        for i in date_range:

           # self.model = self.model.append(current_load)
            self.model = self.model.fit()
            predictions = self.model.predict(start=i, end=end_date, typ='levels') 

            self.model = ARIMA(order=self.order)
            self.model = self.model.fit()
            
            #forecast = self.model.forecast(steps=1) #forecastar ett steg i taget
            #predictions.append(forecast[0])
        #predictions = np.array(predictions)
        #predictions = self.model.predict(start=start_date, end=end_date, typ='levels') 
        return predictions

        # create a differenced series

    def generate_predictions420(self, start_date, end_date):

        if self.model is None:
            raise ValueError("Model has not been trained yet.")

        date_range = pd.date_range(start=start_date, end=end_date, freq='1T')
        predictions = []

        for current_timestamp in date_range:
            self.model = self.model.fit()
            prediction = self.model.predict(start=current_timestamp, end=end_date, typ='levels')
            predictions.append(prediction)

        return predictions




    def generate_predictions2(self, df):
        if self.model is None:
            raise ValueError("Model has not been trained yet.")

        X = df['applied_load'].values
        size = int(len(X) * 0.66)
        df_test = X[size:]
        X = df_test['applied_load'].values
        predictions = []
        for x in X:
            
            output = self.model.forecast(steps=1)
            yhat = output[0]
            predictions.append(yhat)
        
        return predictions
    

    def generate_predictions1(self, df_test):
       
        #df = self.generate_X_values(start_date, end_date)
        X = df_test['applied_load'].values
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