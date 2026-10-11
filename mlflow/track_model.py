import mlflow
import mlflow.sklearn
import joblib

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score
)

MODEL_PATH = "random_forest_ddos_model.pkl"
FEATURES_PATH = "model_features.pkl"

EXPERIMENT_NAME = "cyber-threat-ddos-detection"


def main():
    mlflow.set_experiment(EXPERIMENT_NAME)

    model = joblib.load(MODEL_PATH)
    model_features = joblib.load(FEATURES_PATH)

    with mlflow.start_run():

        mlflow.log_param(
            "model_type",
            "RandomForestClassifier"
        )

        mlflow.log_param(
            "number_of_features",
            len(model_features)
        )

        mlflow.log_param(
            "n_estimators",
            model.n_estimators
        )

        mlflow.log_param(
            "random_state",
            model.random_state
        )

        mlflow.log_metric(
            "validation_accuracy",
            0.9999402307094615
        )

        mlflow.log_metric(
            "validation_precision",
            1.0
        )

        mlflow.log_metric(
            "validation_recall",
            0.9998958441828976
        )

        mlflow.log_metric(
            "validation_f1",
            0.999947919379199
        )

        mlflow.log_metric(
            "test_accuracy",
            0.999880461418923
        )

        mlflow.log_metric(
            "test_precision",
            0.9999479166666667
        )

        mlflow.log_metric(
            "test_recall",
            0.9998437662743465
        )

        mlflow.log_metric(
            "test_f1",
            0.999895838758398
        )

        mlflow.sklearn.log_model(
            sk_model=model,
            name="random_forest_ddos_model",
            skops_trusted_types=[
                "sklearn.tree._tree.Tree"
            ]
        )

        mlflow.log_artifact(
            FEATURES_PATH
        )

        print("Modelo registrado no MLflow com sucesso.")


if __name__ == "__main__":
    main()