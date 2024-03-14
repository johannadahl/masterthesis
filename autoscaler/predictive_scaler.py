# predictive_scaler.py

from flask import Flask, request, jsonify
from predictor import Predictor  # SKAPA EN FIL FÖR ARIMA, XGBOOST OSV OCH SE TILL ATT DE ALLA HAR EN FUNCTION SOM HETER PREDICT LOAD
import pandas as pd
import matplotlib.pyplot as plt
from XGBoost_predictor import XGBoostPredictor

app = Flask(__name__)

predictor = Predictor()
xgboost_predictor = XGBoostPredictor()

@app.route("/predict", methods=["POST"])
def predict():
    data = request.json 
    #när man startar target servicen med start_date och end_date så kanske  
   # predicted_load = predict_load(current_time)
    

   # return jsonify({"predicted_load": predicted_load})

if __name__ == "__main__":
    df = predictor.import_historical_dataset()
    print(df)
    processed = predictor.preprocess_data(df)
    filtered = predictor.remove_outliers(processed)
    filtered.plot(style=".",figsize=(15,5))
    plt.show()
    

    #app.run(debug=True, port=8010,host='0.0.0.0',use_reloader=False)  # Oklart hu