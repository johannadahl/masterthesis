import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
import matplotlib.pyplot as plt

def generate_data(num_samples):
    data = []
    for i in range(num_samples):
        if i % 5 == 0:
            target = np.random.randint(7, 16)
        else:
            target = np.random.randint(0, 4)
        data.append(target)
    return np.array(data)

def prepare_dataset(data, look_back=1):
    X, y = [], []
    for i in range(len(data)-look_back):
        X.append(data[i:(i+look_back)])
        y.append(data[i + look_back])
    return np.array(X), np.array(y)

def train_linear_regression(X, y):
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
    plt.xlabel('Actual Values')
    plt.ylabel('Predicted Values')
    plt.legend()
    plt.show()

if __name__ == "__main__":
    # Generate training data
    num_samples = 200
    data = generate_data(num_samples)

    # Prepare dataset for training
    look_back = 1  # Number of previous samples to use as features
    X, y = prepare_dataset(data, look_back)

    # Train and evaluate linear regression model
    train_linear_regression(X, y)
