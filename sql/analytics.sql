-- Total de previsões por classe
SELECT
    class,
    COUNT(*) AS total
FROM predictions
GROUP BY class
ORDER BY total DESC;


-- Probabilidade média por classe
SELECT
    class,
    AVG(probability_benign) AS avg_probability_benign,
    AVG(probability_ddos) AS avg_probability_ddos
FROM predictions
GROUP BY class;


-- Últimas previsões registradas
SELECT
    id,
    prediction,
    class,
    probability_benign,
    probability_ddos,
    created_at
FROM predictions
ORDER BY created_at DESC
LIMIT 10;


-- Total geral de previsões
SELECT
    COUNT(*) AS total_predictions
FROM predictions;


-- Quantidade de alertas DDoS
SELECT
    COUNT(*) AS total_ddos_alerts
FROM predictions
WHERE class = 'DDoS';