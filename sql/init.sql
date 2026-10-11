CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    prediction SMALLINT NOT NULL,
    class VARCHAR(20) NOT NULL,
    probability_benign DOUBLE PRECISION NOT NULL,
    probability_ddos DOUBLE PRECISION NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE OR REPLACE VIEW prediction_summary AS
SELECT
    class,
    COUNT(*) AS total_predictions,
    AVG(probability_benign) AS avg_probability_benign,
    AVG(probability_ddos) AS avg_probability_ddos,
    MAX(created_at) AS last_prediction_at
FROM predictions
GROUP BY class;
