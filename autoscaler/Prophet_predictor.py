##Script to create  a Prophet-Predictor Class Object
from predictor import Predictor
from prophet import Prophet
from sklearn.metrics import mean_absolute_error
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import warnings
warnings.filterwarnings("ignore")
from pandas.api.types import CategoricalDtype
cat_type = CategoricalDtype(categories=['Monday','Tuesday',
                                        'Wednesday',
                                        'Thursday','Friday',
                                        'Saturday','Sunday'],
                            ordered=True)



class ProphetPredictor(Predictor):
    """""
    Prophet Predictor Class. Uses Facebooks prohpet forecasting. 
    """""
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
        X = df[['applied_load','hour','dayofweek','weekday',
            ]]
        if label:
            y = df[label]
            return X, y
        return X
    
    def add_lags_prophet(self,df):
        target_map = df['applied_load'].to_dict()
        df['lag1'] = (df.index - pd.Timedelta('1 days')).map(target_map)
        df['lag2'] = (df.index - pd.Timedelta('7 days')).map(target_map)
        df['lag3'] = (df.index - pd.Timedelta('14 days')).map(target_map)
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
        .rename(columns={'timestamp':'ds',
                        'applied_load':'y'})
        return train_prophet
    
    def create_model(self,train):
        model = Prophet()
        model.fit(train)
        self.model = model
        return model
    
    def make_predictions(self,test):
        test.index.names = ["timestamp"]
        targetdevice_test_prophet = test.reset_index() \
        .rename(columns={'timestamp':'ds',
                        'applied_load':'y'})
        targetdevice_test_fcst = self.model.predict(targetdevice_test_prophet)
        return targetdevice_test_fcst

    def plot_weekday_load(self,features_and_target ):
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.boxplot(data=features_and_target.dropna(),
                    x='hour',
                    y='applied_load',
                    hue='weekday',
                    ax=ax,
                    linewidth=1)
        ax.set_title('Load on the ClarkNet server per hour per day.')
        ax.set_xlabel('Hour per day')
        ax.set_ylabel('Workload')
        ax.legend(bbox_to_anchor=(1, 1))
        plt.show()
    
    def plot_trends(self,forecast):
        fig = self.model.plot_components(forecast)
        plt.show()


