import random
import time

#### OBS denna slutas aldrig köra mo man inte säger nåt så man måste avsluta genom control c

# ger en siffra mellan (0-3) varje sekund. ger en siffra mellan (7-14) var 5:te sekund

""" def test_print_numbers():

    seconds =1
    statistics = []
    while True:

        if int(time.time()) % 5 == 0:
            number = random.randint(7, 15)
            print(seconds, f'Every 5 seconds: {number}')
            statistics.append(number)
            print(statistics)


        if int(time.time()) % 5 != 0:
            number = random.randint(0, 3)
            print(seconds, f'Every second: {number}')
            statistics.append(number)
        
        seconds+=1
        # vänta 1 sekund
        time.sleep(1)
        print("sleep")


test_print_numbers()
 """

import random
import time
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
import matplotlib.pyplot as plt

def generate_data(num_samples):
    data = []
    for _ in range(num_samples):
        timestamp = int(time.time())
        feature = timestamp % 5  # Feature based on time (0-4)
        if feature == 0:
            target = random.randint(7, 15)
        else:
            target = random.randint(0, 3)
        data.append((feature, target))
        time.sleep(1)
    return np.array(data)

def train_linear_regression(data):
    X = data[:, 0].reshape(-1, 1)  # Feature
    y = data[:, 1]  # Target

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = LinearRegression()
    model.fit(X_train, y_train)

    # Make predictions on the test set
    y_pred = model.predict(X_test)

    # Evaluate the model
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    print(f'Mean Squared Error: {mse}')
    print(f'R-squared Score: {r2}')

    # Plot the predictions vs. actual values
    plt.scatter(X_test, y_test, color='black', label='Actual')
    plt.plot(X_test, y_pred, color='blue', linewidth=3, label='Predicted')
    plt.xlabel('Time Feature')
    plt.ylabel('Load (Target)')
    plt.legend()
    plt.show()

if __name__ == "__main__":
    # Generate dataset
    num_samples = 100
    dataset = generate_data(num_samples)

    # Train and evaluate linear regression model
    train_linear_regression(dataset)
