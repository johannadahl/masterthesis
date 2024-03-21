from predictor import Predictor
import xgboost as xgb
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_squared_error
import seaborn as sns

color_pal = sns.color_palette()

class XGBoostPredictor(Predictor):
    def __init__(self):
        self.model = None

    def create_features(self,df):
        """
        Create time series features based on time series index.
        """
        df = df.copy()
        df['hour'] = df.index.hour
        df['dayofweek'] = df.index.dayofweek
        return df
    
    def split_train_test_sets(self,df):
        train = df.loc[df.index <= "1998-05-25 00:00:00"] #Hitta bättre lösning jao
        test = df.loc[(df.index > "1998-05-25 00:00:00")]
        return train,test
    
    def split_X_and_Y(self,train,test):
        FEATURES = ['hour', 'dayofweek','lag1','lag2','lag3']
        TARGET = 'applied_load'

        X_train = train[FEATURES]
        y_train = train[TARGET]

        X_test = test[FEATURES]
        y_test = test[TARGET]
        return X_train, y_train, X_test, y_test

    def train_model(self,X_train, y_train, X_test, y_test):
        reg = xgb.XGBRegressor(n_estimators = 2000, early_stopping_rounds = 50,learning_rate=0.01,
        enable_categorical = True)
        reg.fit(X_train, y_train,
        eval_set=[(X_train, y_train), (X_test, y_test)],
        verbose=100)
        self.model = reg
        return reg

    def plot_cross_validation_folds(self,df,splits,test_size,gap):
        tss = TimeSeriesSplit(n_splits=splits, test_size=test_size, gap=gap)
        fold = 0
        preds = []
        scores = []
        fig, axs = plt.subplots(10, 1, figsize=(15, 15), sharex=True)

        fold = 0
        for train_idx, val_idx in tss.split(df):
            train = df.iloc[train_idx]
            test = df.iloc[val_idx]
            train['applied_load'].plot(ax=axs[fold],
                                label='Training Set',
                                title=f'Data Train/Test Split Fold {fold}')
            test['applied_load'].plot(ax=axs[fold],
                                label='Test Set')
            axs[fold].axvline(test.index.min(), color='black', ls='--')
            fold += 1
        plt.show()

    def preform_cross_validation(self,df):
        tss = TimeSeriesSplit(n_splits=10, test_size=24, gap=24)
        fold = 0
        preds = []
        scores = []
        self.plot_cross_validation_folds(df,10,24,0) #To se the folds
        for train_idx, val_idx in tss.split(df):
            train = df.iloc[train_idx]
            test = df.iloc[val_idx]

            train = self.create_features(train)
            test = self.create_features(test)

            FEATURES = ['hour', 'dayofweek',
                        'lag1','lag2','lag3']
            TARGET = 'applied_load'
            X_train = train[FEATURES]
            y_train = train[TARGET]

            X_test = test[FEATURES]
            y_test = test[TARGET]

            reg = xgb.XGBRegressor(base_score=0.5, booster='gbtree',    
                                n_estimators=2000,
                                early_stopping_rounds=50,
                                objective='reg:linear',
                                max_depth=3,
                                learning_rate=0.01)
            reg.fit(X_train, y_train,
                    eval_set=[(X_train, y_train), (X_test, y_test)],
                    verbose=100)

            y_pred = reg.predict(X_test)
            preds.append(y_pred)
            score = np.sqrt(mean_squared_error(y_test, y_pred))
            scores.append(score)

        self.model = reg
        return reg, preds, scores

    def add_lag_filters(self,df):
        target_map = df['applied_load'].to_dict()
        ##Här får vi antingen lägga till en if sats eller anta att vi alltid har tillgång till tre veckors data 
        ## De kommer dokc inte funka på clarknet och NASA
        df['lag1'] = (df.index - pd.Timedelta('7 days')).map(target_map)
        df['lag2'] = (df.index - pd.Timedelta('14 days')).map(target_map)
        df['lag3'] = (df.index - pd.Timedelta('21 days')).map(target_map)
        return df
    
    def show_feature_importance(self,reg):
        fi = pd.DataFrame(data=reg.feature_importances_,
             index=reg.feature_names_in_,
             columns=['importance'])
        fi.sort_values('importance').plot(kind='barh', title='Feature Importance')
        plt.show()
            
    def visualize_predictions(self,reg,test,X_test,df):
        test['prediction'] = reg.predict(X_test)
        df = df.merge(test[['prediction']], how='left', left_index=True, right_index=True)
        ax = df[['applied_load']].plot(figsize=(15, 5))
        df['prediction'].plot(ax=ax, style='.')
        plt.legend(['Truth Data', 'Predictions'])
        ax.set_title('Raw Dat and Prediction')
        print(df)
        plt.show()
    
    def visualize_CV_predictions(self,reg,df):
        FEATURES = ['hour', 'dayofweek',
                'lag1','lag2','lag3']
        
        df['pred'] = reg.predict(df[FEATURES])

        df['applied_load'].plot(figsize=(10, 5),
                                    color=color_pal[2],
                                    ms=2,
                                    lw=2,)
        df['pred'].plot(figsize=(10, 5),
                                    color=color_pal[3],
                                    ms=1,
                                    lw=1,
                                    title='Target Service predictions')
        plt.legend(['Historical data workload/hour ','Predictions using XGBoost regressor'])

        plt.show()
    
    def predict_and_plot_future(self, df_and_future,reg):
        FEATURES = ['hour', 'dayofweek',
                'lag1','lag2','lag3']
        future_w_features = df_and_future.query('isFuture').copy()

        future_w_features['pred'] = reg.predict(future_w_features[FEATURES])

        df_and_future['applied_load'].plot(figsize=(10, 5),
                                    color=color_pal[2],
                                    ms=1,
                                    lw=1,)
        future_w_features['pred'].plot(figsize=(10, 5),
                                    color=color_pal[3],
                                    ms=1,
                                    lw=1,
                                    title='Worldcup98 Predictions')

        plt.legend(['Predictions using XGBoost regressor','Historical data'])
        plt.show()