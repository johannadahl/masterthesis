
from flask import Flask, request
import numpy as np
from XGBoost_predictor import XGBoostPredictor
from Prophet_predictor import ProphetPredictor
from autoarima_predicter import ARIMAPredictor
import threading

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
   # df_predictions = generate_predictions_with_xgboost(start_date, end_date)
    #df_predictions = generate_predictions_with_prophet(start_date, end_date)
    df_predictions = generate_predictions_with_arima(start_date, end_date)
    payload = df_predictions.reset_index().to_json(orient='records')
    return payload

    
def create_and_train_xgboost_predictor():
    df = xgboost_predictor.import_historical_dataset()
    if df is not None:
        df = xgboost_predictor.preprocess_data(df)
        df = xgboost_predictor.remove_outliers(df)
        df = xgboost_predictor.create_features(df)
        df = xgboost_predictor.add_lag_filters(df)
        prediction_model, predictions, scores = xgboost_predictor.preform_cross_validation(df)
        print(f'Score across folds {np.mean(scores):0.4f}')
        print(f'Fold scores:{scores}')
    #    xgboost_predictor.visualize_CV_predictions(xgboost_predictor.model,df)
    return xgboost_predictor

def generate_predictions_with_xgboost(start_date, end_date):
    df = xgboost_predictor.generate_X_values(start_date, end_date)
    df = xgboost_predictor.create_features(df)
    df['applied_load'] = None
    df = xgboost_predictor.add_lag_filters(df) 
    df_with_predictions = xgboost_predictor.predict_load(xgboost_predictor.model, df)
    df_with_predictions.drop(columns=df.columns.difference(['pred']), inplace=True)
    return df_with_predictions

   
def create_and_train_prophet_predictor():
    df = prophet_predictor.import_historical_dataset()
    if df is not None:
        df = prophet_predictor.preprocess_data(df)
        df = prophet_predictor.remove_outliers(df)
        df = prophet_predictor.create_features(df)
        df = prophet_predictor.add_lags_prophet(df)
        df = prophet_predictor.fix_prophet_format(df)
        model = prophet_predictor.create_model(df)
    return model

def generate_predictions_with_prophet(start_date, end_date):
    df = prophet_predictor.generate_X_values(start_date, end_date)
    df['applied_load'] = None
    df = prophet_predictor.create_features(df)
    df = prophet_predictor.add_lags_prophet(df) 
    df_with_predictions = prophet_predictor.make_predictions(df)
    df_with_predictions.drop(columns=df_with_predictions.columns.difference(['ds','yhat']), inplace=True)
    df_with_predictions.rename(columns={"yhat": "pred","ds":"index" }, inplace=True)
    return df_with_predictions

def create_and_train_arima_predictor():
    df = arima_predictor.import_historical_dataset()
    if df is not None:
        df = arima_predictor.preprocess_data(df)
        df = arima_predictor.remove_outliers(df)
        model = arima_predictor.train_model(df)
        
    return model

def generate_predictions_with_arima(start_date, end_date):
    df = arima_predictor.generate_X_values(start_date, end_date)
    df['applied_load'] = None
    predictions = arima_predictor.generate_predictions(df)
    return predictions



def start_flask():
    app.run(debug=False, port=8010,use_reloader=False, host='0.0.0.0') #Startar flask server för TargetService på en annan tråd! 

if __name__ == "__main__":
    """""
    Här tränas först modellerna innan servern startas! Sen kan severn bara igång om man vill testa lite olika target service värden.
    """"" 
    #create_and_train_xgboost_predictor()
    #create_and_train_prophet_predictor()
    create_and_train_arima_predictor()
    flask_thread = threading.Thread(target=start_flask) #Flaskservern måste köras på en egen tråd! annars kan man inte köra annan kod samtidigt 
    flask_thread.start()
