from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
import sys
import os

# Add the project root directory to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from plugins.helpers.data_processing import download_files, parse_files, save_to_db

# Default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

# Create the DAG
with DAG(
    'scraping_dag',
    default_args=default_args,
    description='A DAG to download and process weather and currency data',
    schedule_interval=timedelta(hours=1),
    catchup=False,
    max_active_runs=1,
) as dag:
    
    # Create PostgreSQL tables if they don't exist
    create_weather_table = PostgresOperator(
        task_id='create_weather_table',
        postgres_conn_id='postgres_default',
        sql="""
        CREATE TABLE IF NOT EXISTS weather_data (
            id SERIAL PRIMARY KEY,
            temperature_c DECIMAL(5,2),
            timestamp TIMESTAMP
        );
        """
    )

    create_currency_table = PostgresOperator(
        task_id='create_currency_table',
        postgres_conn_id='postgres_default',
        sql="""
        CREATE TABLE IF NOT EXISTS currency_data (
            id SERIAL PRIMARY KEY,
            usd_to_cny DECIMAL(10,4),
            timestamp TIMESTAMP
        );
        """
    )

    # Define the tasks
    download_task = PythonOperator(
        task_id='download_files',
        python_callable=download_files,
        provide_context=True
    )

    parse_task = PythonOperator(
        task_id='parse_files',
        python_callable=parse_files,
        provide_context=True
    )

    save_task = PythonOperator(
        task_id='save_to_db',
        python_callable=save_to_db,
        provide_context=True
    )

    # Set task dependencies
    create_weather_table >> create_currency_table >> download_task >> parse_task >> save_task
