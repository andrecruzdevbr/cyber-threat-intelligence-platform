import json
import time
import pandas as pd
from kafka import KafkaProducer


DATASET_PATH = "CICIDS2017_DDoS_Silver.parquet"
KAFKA_BROKER = "localhost:29092"
TOPIC = "network-traffic"

EVENTS_PER_CLASS = 20
INTERVAL_SECONDS = 1


producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda value: json.dumps(value).encode("utf-8")
)


df = pd.read_parquet(DATASET_PATH)

benign_df = (
    df[df["Label"] == "BENIGN"]
    .sample(n=EVENTS_PER_CLASS, random_state=42)
    .reset_index(drop=True)
)

ddos_df = (
    df[df["Label"] == "DDoS"]
    .sample(n=EVENTS_PER_CLASS, random_state=42)
    .reset_index(drop=True)
)


events = []

for i in range(EVENTS_PER_CLASS):
    events.append(benign_df.iloc[i])
    events.append(ddos_df.iloc[i])


for number, row in enumerate(events, start=1):
    event = row.to_dict()

    producer.send(
        TOPIC,
        value=event
    )

    producer.flush()

    print(
        f"Evento {number:02d} enviado | "
        f"Classe real: {event['Label']} | "
        f"Destino: {event['Destination Port']}"
    )

    time.sleep(INTERVAL_SECONDS)


producer.close()

print("\nEnvio concluído.")