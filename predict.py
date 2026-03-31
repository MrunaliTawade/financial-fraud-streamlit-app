import joblib
import numpy as np
import os

# Load model safely
model_path = os.path.join(os.path.dirname(__file__), "model.pkl")
model = joblib.load(model_path)

def predict_transaction(data):
    """
    data = [
        type, amount, oldbalanceOrg,
        newbalanceOrig, oldbalanceDest, newbalanceDest
    ]
    """

    if len(data) != 8:
        raise ValueError("Input must have 6 features")

    data = np.array(data).reshape(1, -1)
    result = model.predict(data)

    return int(result[0])

