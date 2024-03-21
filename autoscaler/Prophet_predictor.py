##Script to create  a Prophet-Predictor Class Object
from predictor import Predictor
from prophet import Prophet
from sklearn.metrics import mean_absolute_error
import matplotlib 
import matplotlib.pyplot as plt
plt.style.use('ggplot')
plt.style.use('fivethirtyeight')
import pandas as pd


import warnings
warnings.filterwarnings("ignore")
from pandas.api.types import CategoricalDtype
cat_type = CategoricalDtype(categories=['Monday','Tuesday',
                                        'Wednesday',
                                        'Thursday','Friday',
                                        'Saturday','Sunday'],
                            ordered=True)



class ProphetPredictor(Predictor):
    def __init__(self):
        self.model = None

    def create_features(self, df, label=None):
        """
        Creates time series features from datetime index.
        """
        df = df.copy()
        df['date'] = df.index
        df['hour'] = df['date'].dt.hour
        df['dayofweek'] = df['date'].dt.dayofweek
        df['weekday'] = df['date'].dt.day_name()
        df['weekday'] = df['weekday'].astype(cat_type)
        X = df[['hour','dayofweek','weekday',
            ]]
        if label:
            y = df[label]
            return X, y
        return X
    
    def add_lags_prophet(self,df):
        target_map = df['applied_load'].to_dict()
        df['lag1'] = (df.index - pd.Timedelta('7 days')).map(target_map)
        df['lag2'] = (df.index - pd.Timedelta('14 days')).map(target_map)
        df['lag3'] = (df.index - pd.Timedelta('21 days')).map(target_map)
        return df
    
    def split_train_test(self, df, split_date):
        train = df.loc[df.index <= split_date].copy()
        test = df.loc[df.index > split_date].copy()
        return train, test
    
    def fix_prophet_format(self, df):
        # Format data for prophet model using ds and y
        # Prophet model expects the dataset to be named a specific way. We will rename our dataframe columns before feeding it into the model.
        # Datetime column named: ds
        # target : y
        train_prophet = df.reset_index() \
        .rename(columns={'index':'ds',
                        'applied_load':'y'})
        return train_prophet
    
    def create_model(self,train):
        model = Prophet()
        model.fit(train)
        self.model = model
        return model
    
