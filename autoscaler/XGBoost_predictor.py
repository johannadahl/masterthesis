from predictor import Predictor
import xgboost as xgb
import matplotlib.pyplot as plt
import pandas as pd


class XGBoostPredictor(Predictor):
    def __init__(self):
        self.model = "XGBoost"

    def create_features(self,df):
        """
        Create time series features based on time series index.
        """
        df = df.copy()
        df['hour'] = df.index.hour
        df['dayofweek'] = df.index.dayofweek
        return df
    
    def split_train_test_sets(self,df):
        train = df.loc[df.index <= "1998-06-23 00:00:00"] #Hitta bättre lösning jao
        test = df.loc[(df.index > "1998-06-23 00:00:00")]
        train = self.create_features_xgboost(train)
        test = self.create_features_xgboost(test)

        FEATURES = ['hour', 'dayofweek']
        TARGET = 'total_load'

        X_train = train[FEATURES]
        y_train = train[TARGET]

        X_test = test[FEATURES]
        y_test = test[TARGET]
        return X_train, y_train, X_test, y_test
    
    def show_feature_importance(self,reg,df):
        fi = pd.DataFrame(data=reg.feature_importances_,
             index=reg.feature_names_in_,
             columns=['importance'])
        fi.sort_values('importance').plot(kind='barh', title='Feature Importance')
        plt.show()

    def train_model(self,X_train, y_train, X_test, y_test):
        reg = xgb.XGBRegressor(n_estimators = 2000, early_stopping_rounds = 50,learning_rate=0.01,
        enable_categorical = True)
        reg.fit(X_train, y_train,
        eval_set=[(X_train, y_train), (X_test, y_test)],
        verbose=100)
        self.reg = reg
        return reg
    

    def preform_cross_validation(self):
        """
        .
        """

    def generate_lag_filters(self):
        """
        .
        """

