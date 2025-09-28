from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime


def dummy_task(**kwargs):
    """Placeholder task for nightly bulk refresh."""
    print("Dummy task for nightly bulk refresh")


with DAG(
    dag_id="dump_refresh_dag",
    start_date=datetime(2025, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    tags=["nutriscan"],
) as dag:
    refresh_task = PythonOperator(
        task_id="refresh_data",
        python_callable=dummy_task,
    )
