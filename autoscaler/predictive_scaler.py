# predictive_scaler.py

from flask import Flask, request, jsonify
from predictor import Predictor  # SKAPA EN FIL FÖR ARIMA, XGBOOST OSV OCH SE TILL ATT DE ALLA HAR EN FUNCTION SOM HETER PREDICT LOAD
import numpy as np
from XGBoost_predictor import XGBoostPredictor

app = Flask(__name__)

@app.route("/predict", methods=["POST"])
def predict():
    data = request.json 
    #när man startar target servicen med start_date och end_date så kanske  
   # predicted_load = predict_load(current_time)
    

   # return jsonify({"predicted_load": predicted_load})
    
def predict_with_xgboost():
    xgboost_predictor = XGBoostPredictor()
    df = xgboost_predictor.import_historical_dataset()
    df = xgboost_predictor.preprocess_data(df)
    df = xgboost_predictor.remove_outliers(df)
    df = xgboost_predictor.create_features(df)
    df = xgboost_predictor.add_lag_filters(df)
    prediction_model, predictions, scores = xgboost_predictor.preform_cross_validation(df)
    print(f'Score across folds {np.mean(scores):0.4f}')
    print(f'Fold scores:{scores}')
    xgboost_predictor.visualize_CV_predictions(prediction_model,df)
   

if __name__ == "__main__":
    predict_with_xgboost()


    #app.run(debug=True, port=8010,host='0.0.0.0',use_reloader=False)  # Oklart hu