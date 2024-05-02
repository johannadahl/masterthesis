
from flask import Flask, request
import numpy as np
from XGBoost_predictor import XGBoostPredictor
from Prophet_predictor import ProphetPredictor
from autoarima_predicter import ARIMAPredictor
import threading
import pandas as pd
import matplotlib.pyplot as plt

app = Flask(__name__)
xgboost_predictor = XGBoostPredictor()
prophet_predictor = ProphetPredictor()
arima_predictor = ARIMAPredictor()

@app.route("/predict", methods=["POST"])
def predict():
    """""
    Här kommer man när target service startar. Den skickar en request om vad predikterade värderna är för loaden som kommer börja köras på systemet. 
    """""
    start_date = request.json.get('start_date', None)
    end_date = request.json.get('end_date', None)
    """""
    Ändrade det här, så nu är det bara en rad som man måste "ändra" om man vill byta prediktionsmodell (kommentera ut de som inte ska användas)
    Detta kan struktureras upp bättre sen med args men funkar så länge,
    """""
    df_predictions = generate_predictions_with_arima(start_date, end_date)
   # df_predictions = generate_predictions_with_xgboost(start_date, end_date)
   # df_predictions = generate_predictions_with_prophet(start_date, end_date)
    payload = df_predictions.reset_index().to_json(orient='records')
    return payload

    
def create_and_train_xgboost_predictor():
    df = xgboost_predictor.import_historical_dataset()
    if df is not None:
        df = xgboost_predictor.preprocess_data(df)
        df = xgboost_predictor.remove_outliers(df)
        df = xgboost_predictor.create_features(df)
        df = xgboost_predictor.add_lag_filters(df)
        splits = 7
        prediction_model, predictions, scores = xgboost_predictor.preform_cross_validation(df,splits,1440,24)
        print(f'Score across folds {np.mean(scores):0.4f}')
        print(f'Fold scores:{scores}')
   #  #   xgboost_predictor.show_feature_importance(xgboost_predictor.model,df)
        xgboost_predictor.visualize_CV_predictions(xgboost_predictor.model,df,splits)
        #best_params, best_score = xgboost_predictor.optimize_hyperparameters(df)
        #print(best_params,best_score)
    return xgboost_predictor

def generate_predictions_with_xgboost(start_date, end_date):
    df = xgboost_predictor.generate_X_values(start_date, end_date)
    df = xgboost_predictor.create_features(df)
    df = xgboost_predictor.add_lag_filters(df) 
    df_with_predictions = xgboost_predictor.predict_load(xgboost_predictor.model, df)
    df_with_predictions.drop(columns=df_with_predictions.columns.difference(['pred']), inplace=True)
    df_with_predictions.sort_index(inplace=True)
    df_with_predictions = df_with_predictions[~df_with_predictions.index.duplicated(keep='last')]
    end_date_dt = pd.to_datetime(end_date)
    df_predictions = df_with_predictions.loc[start_date:end_date_dt - pd.Timedelta(minutes=1)] 
    return df_predictions

def create_and_train_prophet_predictor():
    df = prophet_predictor.import_historical_dataset()
    if df is not None:
        df = prophet_predictor.preprocess_data(df)
        df = prophet_predictor.remove_outliers(df)
        df = prophet_predictor.create_features(df)
     #   prophet_predictor.plot_weekday_load(df)
        df = prophet_predictor.add_lags_prophet(df)
        df = prophet_predictor.fix_prophet_format(df)
        model = prophet_predictor.create_model(df)
     #   model = prophet_predictor.hypertune_parameters(df)
        return model
    else:
        return None

def generate_predictions_with_prophet(start_date, end_date):
    df = prophet_predictor.generate_X_values(start_date, end_date)
    df['applied_load'] = None
    if prophet_predictor.model is not None:
        df = prophet_predictor.create_features(df)
        df = prophet_predictor.add_lags_prophet(df) 
        df_with_predictions = prophet_predictor.make_predictions(df)
       # prophet_predictor.plot_trends(df_with_predictions)
        df_with_predictions.rename(columns={"yhat": "pred","ds":"index" }, inplace=True)     
        df_with_predictions.set_index("index", inplace=True)   
        df_with_predictions = df_with_predictions.drop(columns=df_with_predictions.columns.difference(['pred']))
        df_with_predictions = df_with_predictions.sort_index()
        df_with_predictions = df_with_predictions[~df_with_predictions.index.duplicated(keep='last')]
        end_date_dt = pd.to_datetime(end_date)
        df_predictions = df_with_predictions.loc[start_date:end_date_dt - pd.Timedelta(minutes=1)]
        return df_predictions
    else:
        return df

def create_and_train_arima_predictor():
    df = arima_predictor.import_historical_dataset()
   # df = arima_predictor.generate_X_values("1995-07-01", "1995-07-31")
    if df is not None:
        df = arima_predictor.preprocess_data(df)
        df = arima_predictor.remove_outliers(df)
        print("den som de tränas på", df)
        model = arima_predictor.train_model(df)
        #arima_predictor.validate_model(df)
    return model

def generate_predictions_with_arima(start_date, end_date):
    print("I GENERATE PREDICTIONS")
    predictions = arima_predictor.generate_predictions(start_date, end_date)

    ##Prediktions kommer per 60:e min, här resamplar vi för att få varje minut
    upsampled_predictions = predictions.resample('T').mean()

    #Interpolering för att få punkter mellan punkter
    interpolated_predictions = upsampled_predictions.interpolate(method='linear')
    print("i generate predictions", interpolated_predictions)
    interpolated_predictions_df = interpolated_predictions.to_frame()
    interpolated_predictions_df.columns = ['pred']
    print(interpolated_predictions_df)
    end_date_dt = pd.to_datetime(end_date)
    start_date_dt = pd.to_datetime(start_date)
    df_predictions = interpolated_predictions_df.loc[start_date_dt:end_date_dt - pd.Timedelta(minutes=1)]
    print(df_predictions)
    return df_predictions

def generate_forecast_with_arima():
    """
    Används ej
    """
    df_predictions, pred_mean, forecast_ci = arima_predictor.generate_forecast()
    return df_predictions, pred_mean, forecast_ci

def visualize_arima_forecast():
    """
    Används ej
    """
    df = arima_predictor.import_historical_dataset()
    df = arima_predictor.preprocess_data(df)
    df = arima_predictor.remove_outliers(df)
   # split_index = int(0.66 * len(df))
   # train_df = df.iloc[:split_index]
   # test_df = df.iloc[split_index:]
    X_train = df['applied_load']
    predictions, pred_mean, forecast_ci = generate_forecast_with_arima()
    df_predictions = arima_predictor.generate_predictions("1995-07-01","1995-07-20")
    upsampled_predictions = df_predictions.resample('T').mean()

    # Perform linear interpolation to fill in the missing values
    interpolated_predictions = upsampled_predictions.interpolate(method='linear')
    print("predictions", df_predictions)
    print("interpolated predictions", interpolated_predictions)
    # Plot the forecast
    plt.figure(figsize=(12, 6))
    plt.plot(X_train, label='Observed')
    plt.plot(pred_mean, label='Forecast', color='red')
    plt.plot(df_predictions, label='Predicted')
    plt.plot(interpolated_predictions, label='interpolated predicted')
    plt.fill_between(forecast_ci.index, forecast_ci.iloc[:, 0], forecast_ci.iloc[:, 1], color='pink')
    plt.title("workload Forecast")
    plt.xlabel("Timestamp")
    plt.ylabel("Workload")
    plt.legend()
    plt.show()

def write_to_latex(df, filename):
    df_tail = df.tail()  # Get the head of the DataFrame
    latex_table = df_tail.to_latex()

    with open(filename, 'w') as f:
        f.write(latex_table)

def start_flask():
    app.run(debug=False, port=8010,use_reloader=False, host='0.0.0.0') #Startar flask server för TargetService på en annan tråd! 

if __name__ == "__main__":
    """""
    Här tränas först modellerna innan servern startas! Sen kan severn bara igång om man vill testa lite olika target service värden.
    """"" 
   #  create_and_train_xgboost_predictor()
   # generate_predictions_with_xgboost("1995-07-16","1995-07-20")
   # create_and_train_prophet_predictor()
    create_and_train_arima_predictor()
    visualize_arima_forecast()
    flask_thread = threading.Thread(target=start_flask) #Flaskservern måste köras på en egen tråd! annars kan man inte köra annan kod samtidigt 
    flask_thread.start()
