from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator


with DAG(
    dag_id="cyber_threat_pipeline",
    description="Pipeline analítico da plataforma Cyber Threat Intelligence",
    start_date=datetime(2026, 10, 1),
    schedule=None,
    catchup=False,
    tags=["cybersecurity", "dbt", "data-quality"],
) as dag:

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command="""
        cd /opt/airflow/dbt_cyber &&
        dbt run --profiles-dir .
        """,
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command="""
        cd /opt/airflow/dbt_cyber &&
        dbt test --profiles-dir .
        """,
    )

    pipeline_completed = BashOperator(
        task_id="pipeline_completed",
        bash_command='echo "Cyber Threat pipeline concluído com sucesso."',
    )

    dbt_run >> dbt_test >> pipeline_completed