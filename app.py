from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import joblib
import os
import pandas as pd
import psycopg2

from rag.incident_assistant import analyze_incident


app = FastAPI(
    title="Cyber Threat Detection API",
    description="API para classificação de tráfego de rede como BENIGN ou DDoS.",
    version="1.0.0"
)


model = joblib.load("random_forest_ddos_model.pkl")
model_features = joblib.load("model_features.pkl")


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://cyber_user:change_me@localhost:5433/cyber_threat"
)


class PredictionRequest(BaseModel):
    features: dict[str, float]


@app.get("/")
def root():
    return {
        "status": "online",
        "model": "Random Forest",
        "task": "DDoS binary classification"
    }


@app.post("/predict")
def predict(request: PredictionRequest):

    missing_features = [
        feature
        for feature in model_features
        if feature not in request.features
    ]

    if missing_features:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Missing required features.",
                "missing_features": missing_features
            }
        )

    input_df = pd.DataFrame(
        [request.features]
    )

    input_df = input_df[
        model_features
    ]

    prediction = model.predict(
        input_df
    )[0]

    probability = model.predict_proba(
        input_df
    )[0]

    predicted_class = (
        "DDoS"
        if prediction == 1
        else "BENIGN"
    )

    connection = psycopg2.connect(
        DATABASE_URL
    )

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO predictions (
            prediction,
            class,
            probability_benign,
            probability_ddos
        )
        VALUES (%s, %s, %s, %s)
        RETURNING id, created_at
        """,
        (
            int(prediction),
            predicted_class,
            float(probability[0]),
            float(probability[1])
        )
    )

    prediction_id, created_at = (
        cursor.fetchone()
    )

    connection.commit()

    cursor.close()
    connection.close()

    response = {
        "prediction_id": prediction_id,
        "prediction": int(prediction),
        "class": predicted_class,
        "probability_benign": float(
            probability[0]
        ),
        "probability_ddos": float(
            probability[1]
        ),
        "created_at": (
            created_at.isoformat()
        )
    }

    if predicted_class == "DDoS":

        incident_analysis = analyze_incident(
            predicted_class=predicted_class,
            probability_ddos=float(
                probability[1]
            ),
            created_at=created_at.isoformat()
        )

        response[
            "incident_analysis"
        ] = incident_analysis

    return response