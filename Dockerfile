FROM apache/airflow:2.6.3-python3.10

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy DAGs and plugins
COPY dags /opt/airflow/dags
COPY plugins /opt/airflow/plugins
COPY setup.py /opt/airflow/

# Install the plugins package
RUN pip install -e /opt/airflow/

# Create default user
RUN airflow users create \
    --username admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com \
    --password admin
