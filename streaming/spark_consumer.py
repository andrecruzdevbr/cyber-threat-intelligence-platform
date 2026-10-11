import json
import urllib.request

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json
from pyspark.sql.types import StructType, StructField, DoubleType, StringType


# =========================================================
# CONFIGURAÇÕES
# =========================================================

KAFKA_BROKER = "kafka:9092"
TOPIC = "network-traffic"

API_URL = "http://api:8000/predict"

DATA_LAKE_PATH = "/opt/spark/work-dir/data_lake"

BRONZE_PATH = f"{DATA_LAKE_PATH}/bronze"
SILVER_PATH = f"{DATA_LAKE_PATH}/silver"
GOLD_PATH = f"{DATA_LAKE_PATH}/gold"

CHECKPOINT_PATH = f"{DATA_LAKE_PATH}/checkpoints/cyber-threat-streaming"


# =========================================================
# FEATURES DO MODELO
# =========================================================

MODEL_FEATURES = [
    "Destination Port",
    "Flow Duration",
    "Total Fwd Packets",
    "Total Backward Packets",
    "Total Length of Fwd Packets",
    "Total Length of Bwd Packets",
    "Fwd Packet Length Max",
    "Fwd Packet Length Min",
    "Fwd Packet Length Mean",
    "Fwd Packet Length Std",
    "Bwd Packet Length Max",
    "Bwd Packet Length Min",
    "Bwd Packet Length Mean",
    "Bwd Packet Length Std",
    "Flow Bytes/s",
    "Flow Packets/s",
    "Flow IAT Mean",
    "Flow IAT Std",
    "Flow IAT Max",
    "Flow IAT Min",
    "Fwd IAT Total",
    "Fwd IAT Mean",
    "Fwd IAT Std",
    "Fwd IAT Max",
    "Fwd IAT Min",
    "Bwd IAT Total",
    "Bwd IAT Mean",
    "Bwd IAT Std",
    "Bwd IAT Max",
    "Bwd IAT Min",
    "Fwd PSH Flags",
    "Fwd Header Length",
    "Bwd Header Length",
    "Fwd Packets/s",
    "Bwd Packets/s",
    "Min Packet Length",
    "Max Packet Length",
    "Packet Length Mean",
    "Packet Length Std",
    "Packet Length Variance",
    "FIN Flag Count",
    "SYN Flag Count",
    "RST Flag Count",
    "PSH Flag Count",
    "ACK Flag Count",
    "URG Flag Count",
    "ECE Flag Count",
    "Down/Up Ratio",
    "Average Packet Size",
    "Avg Bwd Segment Size",
    "Subflow Bwd Packets",
    "Subflow Bwd Bytes",
    "Init_Win_bytes_forward",
    "Init_Win_bytes_backward",
    "act_data_pkt_fwd",
    "min_seg_size_forward",
    "Active Mean",
    "Active Std",
    "Active Max",
    "Active Min",
    "Idle Mean",
    "Idle Std",
    "Idle Max",
    "Idle Min",
]


# =========================================================
# SPARK
# =========================================================

spark = (
    SparkSession.builder
    .appName("CyberThreatIntelligenceStreaming")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")


# =========================================================
# SCHEMA DOS EVENTOS
# =========================================================

schema = StructType(
    [StructField(feature, DoubleType(), True) for feature in MODEL_FEATURES]
    + [StructField("Label", StringType(), True)]
)


# =========================================================
# LEITURA DO KAFKA
# =========================================================

kafka_stream = (
    spark.readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", KAFKA_BROKER)
    .option("subscribe", TOPIC)
    .option("startingOffsets", "latest")
    .load()
)


# =========================================================
# EVENTO BRUTO + PARSE DO JSON
# =========================================================

stream = (
    kafka_stream
    .select(
        col("timestamp").alias("kafka_timestamp"),
        col("partition").alias("kafka_partition"),
        col("offset").alias("kafka_offset"),
        col("value").cast("string").alias("raw_json")
    )
    .withColumn(
        "data",
        from_json(
            col("raw_json"),
            schema
        )
    )
    .select(
        col("kafka_timestamp"),
        col("kafka_partition"),
        col("kafka_offset"),
        col("raw_json"),
        *[
            col(f"data.`{feature}`").alias(feature)
            for feature in MODEL_FEATURES
        ],
        col("data.Label").alias("Label")
    )
)


# =========================================================
# PROCESSAMENTO DE CADA MICRO-BATCH
# =========================================================

def process_batch(batch_df, batch_id):

    if batch_df.isEmpty():
        return

    print(f"\n========== BATCH {batch_id} ==========\n")


    # -----------------------------------------------------
    # BRONZE
    # Guarda o evento exatamente como chegou do Kafka
    # -----------------------------------------------------

    bronze_df = batch_df.select(
        "kafka_timestamp",
        "kafka_partition",
        "kafka_offset",
        "raw_json"
    )

    (
        bronze_df.write
        .mode("append")
        .parquet(BRONZE_PATH)
    )


    # -----------------------------------------------------
    # SILVER
    # Evento já transformado em colunas estruturadas
    # -----------------------------------------------------

    silver_df = batch_df.select(
        "kafka_timestamp",
        "kafka_partition",
        "kafka_offset",
        *[
            col(f"`{feature}`")
            for feature in MODEL_FEATURES
        ],
        col("Label")
    )

    (
        silver_df.write
        .mode("append")
        .parquet(SILVER_PATH)
    )


    # -----------------------------------------------------
    # GOLD
    # Somente dados necessários para ML
    # -----------------------------------------------------

    gold_df = batch_df.select(
        "kafka_timestamp",
        *[
            col(f"`{feature}`")
            for feature in MODEL_FEATURES
        ],
        col("Label")
    )

    (
        gold_df.write
        .mode("append")
        .parquet(GOLD_PATH)
    )


    # -----------------------------------------------------
    # INFERÊNCIA
    # Spark → FastAPI → Random Forest
    # -----------------------------------------------------

    for row in gold_df.toLocalIterator():

        missing_values = [
            feature
            for feature in MODEL_FEATURES
            if row[feature] is None
        ]

        if missing_values:
            print(
                f"Evento ignorado por valores ausentes: "
                f"{missing_values}"
            )
            continue

        features = {
            feature: float(row[feature])
            for feature in MODEL_FEATURES
        }

        payload = json.dumps(
            {
                "features": features
            }
        ).encode("utf-8")

        request = urllib.request.Request(
            API_URL,
            data=payload,
            headers={
                "Content-Type": "application/json"
            },
            method="POST"
        )

        try:

            with urllib.request.urlopen(
                request,
                timeout=10
            ) as response:

                result = json.loads(
                    response.read().decode("utf-8")
                )

                print(
                    f"Real: {row['Label']} | "
                    f"Predição: {result['class']} | "
                    f"P(DDoS): "
                    f"{result['probability_ddos']:.4f}"
                )

        except Exception as error:

            print(
                f"Erro ao enviar evento para API: {error}"
            )


# =========================================================
# INICIALIZAÇÃO DO STREAMING
# =========================================================

query = (
    stream.writeStream
    .foreachBatch(process_batch)
    .option(
        "checkpointLocation",
        CHECKPOINT_PATH
    )
    .start()
)

query.awaitTermination()