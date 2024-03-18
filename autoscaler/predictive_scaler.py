# predictive_scaler.py

from flask import Flask, request, jsonify
from predictor import Predictor  # SKAPA EN FIL FÖR ARIMA, XGBOOST OSV OCH SE TILL ATT DE ALLA HAR EN FUNCTION SOM HETER PREDICT LOAD
import numpy as np
from XGBoost_predictor import XGBoostPredictor
import threading

app = Flask(__name__)
xgboost_predictor = XGBoostPredictor()

@app.route("/predict", methods=["POST"])
def predict():
    data = request.json 
    start_date = request.json.get('start_date', None)
    end_date = request.json.get('end_date', None)
    predicted_load = xgboost_predictor.predict_load(start_date, end_date)
    return jsonify({"predicted_load": predicted_load})

    
def create_and_train_xgboost_predictor():
    df = xgboost_predictor.import_historical_dataset()
    df = xgboost_predictor.preprocess_data(df)
    df = xgboost_predictor.remove_outliers(df)
    df = xgboost_predictor.create_features(df)
    df = xgboost_predictor.add_lag_filters(df)
    prediction_model, predictions, scores = xgboost_predictor.preform_cross_validation(df)
    print(f'Score across folds {np.mean(scores):0.4f}')
    print(f'Fold scores:{scores}')
    xgboost_predictor.visualize_CV_predictions(prediction_model,df)
    return xgboost_predictor

def predict_future_with_xgboost(xgboost_predictor, start_date, end_date):
    df = xgboost_predictor.import_historical_dataset()
    df = xgboost_predictor.preprocess_data(df)
    df = xgboost_predictor.remove_outliers(df)
    future_df, df_and_future = xgboost_predictor.generate_future_values(df,"1998-05-30 00:00:00")
    df_and_future = xgboost_predictor.create_features(df_and_future)
    df_and_future = xgboost_predictor.add_lag_filters(df_and_future)
    print(df_and_future)
    xgboost_predictor.predict_and_plot_future(df_and_future,xgboost_predictor.model)
   
def start_flask():
    app.run(debug=False, port=8010,use_reloader=False, host='0.0.0.0') #Startar flask server för TargetService på en annan tråd! 

if __name__ == "__main__":
    xgboost_predictor = create_and_train_xgboost_predictor()
    flask_thread = threading.Thread(target=start_flask) #Flaskservern måste köras på en egen tråd! annars kan man inte köra annan kod samtidigt 
    flask_thread.start()
   # predict_future_with_xgboost(xgboost_predictor)
