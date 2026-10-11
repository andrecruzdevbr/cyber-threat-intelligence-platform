
from fastapi.testclient import TestClient
from app import app
import joblib

client = TestClient(app)

model_features = joblib.load("model_features.pkl")


def test_root():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["status"] == "online"


def test_missing_features():
    payload = {
        "features": {
            "Destination Port": 80.0,
            "Flow Duration": 1000.0
        }
    }

    response = client.post("/predict", json=payload)

    assert response.status_code == 400
    assert "missing_features" in response.json()["detail"]


def test_valid_prediction():
    payload = {
        "features": {
            feature: 0.0
            for feature in model_features
        }
    }

    response = client.post("/predict", json=payload)

    assert response.status_code == 200

    result = response.json()

    assert "prediction" in result
    assert "class" in result
    assert "probability_benign" in result
    assert "probability_ddos" in result

    assert result["prediction"] in [0, 1]
    assert result["class"] in ["BENIGN", "DDoS"]
