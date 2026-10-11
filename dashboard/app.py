import os
import pandas as pd
import psycopg2
import streamlit as st

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://cyber_user:change_me@localhost:5433/cyber_threat"
)

st.set_page_config(
    page_title="Cyber Threat Intelligence Dashboard",
    page_icon="🛡️",
    layout="wide"
)

st.title("Cyber Threat Intelligence Dashboard")
st.caption("Monitoramento de previsões de tráfego BENIGN e DDoS")


def load_summary():
    connection = psycopg2.connect(DATABASE_URL)

    query = """
    SELECT
        class,
        total_predictions,
        avg_probability_benign,
        avg_probability_ddos,
        last_prediction_at
    FROM prediction_summary;
    """

    df = pd.read_sql(query, connection)
    connection.close()

    return df


def load_recent_predictions():
    connection = psycopg2.connect(DATABASE_URL)

    query = """
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
    """

    df = pd.read_sql(query, connection)
    connection.close()

    return df


summary_df = load_summary()
recent_df = load_recent_predictions()

total_predictions = int(summary_df["total_predictions"].sum())

ddos_total = int(
    summary_df.loc[
        summary_df["class"] == "DDoS",
        "total_predictions"
    ].sum()
)

benign_total = int(
    summary_df.loc[
        summary_df["class"] == "BENIGN",
        "total_predictions"
    ].sum()
)

threat_rate = (
    ddos_total / total_predictions * 100
    if total_predictions > 0
    else 0
)

ddos_avg_probability = summary_df.loc[
    summary_df["class"] == "DDoS",
    "avg_probability_ddos"
]

ddos_avg_probability = (
    float(ddos_avg_probability.iloc[0]) * 100
    if not ddos_avg_probability.empty
    else 0
)

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Total de previsões",
    total_predictions
)

col2.metric(
    "DDoS detectados",
    ddos_total
)

col3.metric(
    "Tráfego BENIGN",
    benign_total
)

col4.metric(
    "Taxa de ameaça",
    f"{threat_rate:.1f}%"
)

if ddos_total > 0:
    st.error(
        f"Alerta: {ddos_total} ocorrência(s) de DDoS detectada(s)."
    )
else:
    st.success(
        "Nenhuma ameaça DDoS detectada."
    )

st.subheader("Distribuição das classes")

chart_df = summary_df.set_index("class")[["total_predictions"]]

st.bar_chart(chart_df)

st.subheader("Indicadores de ameaça")

col5, col6 = st.columns(2)

col5.metric(
    "Confiança média em DDoS",
    f"{ddos_avg_probability:.1f}%"
)

last_ddos = recent_df[
    recent_df["class"] == "DDoS"
]

if not last_ddos.empty:
    last_ddos_time = last_ddos.iloc[0]["created_at"]

    col6.metric(
        "Última detecção DDoS",
        str(last_ddos_time)
    )
else:
    col6.metric(
        "Última detecção DDoS",
        "Nenhuma"
    )

st.subheader("Resumo por classe")

summary_display = summary_df.copy()

summary_display["avg_probability_benign"] = (
    summary_display["avg_probability_benign"] * 100
).round(2)

summary_display["avg_probability_ddos"] = (
    summary_display["avg_probability_ddos"] * 100
).round(2)

st.dataframe(
    summary_display,
    use_container_width=True
)

st.subheader("Últimas previsões")

recent_display = recent_df.copy()

recent_display["probability_benign"] = (
    recent_display["probability_benign"] * 100
).round(2)

recent_display["probability_ddos"] = (
    recent_display["probability_ddos"] * 100
).round(2)

st.dataframe(
    recent_display,
    use_container_width=True
)