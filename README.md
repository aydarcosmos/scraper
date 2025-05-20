# Airflow Scraping Pipeline

This project implements an Airflow DAG that scrapes weather and currency exchange rate data from XML feeds and stores the results in a PostgreSQL database.

## Features

- Downloads XML files from two URLs:
  - Weather data from `https://forecast.weather.gov/xml/current_obs/KJFK.xml`
  - Currency exchange rates from `https://www.floatrates.com/daily/usd.xml`
- Parses XML files to extract:
  - Current temperature in New York (converted to Celsius)
  - USD to CNY exchange rate
- Stores results in PostgreSQL database
- Includes error handling and logging
- Configurable schedule (currently set to run hourly)

## Setup

1. Install required dependencies:
```bash
pip install -r requirements.txt
```

2. Set up PostgreSQL database:
   - Create a PostgreSQL database
   - Configure the connection in Airflow's UI under Admin -> Connections
   - Use connection ID: `postgres_default`

3. Configure Airflow:
   - Ensure Airflow is installed and running
   - Place this DAG file in Airflow's DAGs folder
   - Configure the PostgreSQL connection in Airflow

## DAG Structure

The DAG consists of the following tasks:

1. `create_weather_table`: Creates the weather_data table if it doesn't exist
2. `create_currency_table`: Creates the currency_data table if it doesn't exist
3. `download_files`: Downloads XML files from the specified URLs
4. `parse_files`: Parses the downloaded XML files to extract required data
5. `save_to_db`: Saves the parsed data into the PostgreSQL database

## Data Storage

The data is stored in two PostgreSQL tables:

- `weather_data`:
  - `id`: SERIAL PRIMARY KEY
  - `temperature_c`: DECIMAL(5,2)
  - `timestamp`: TIMESTAMP

- `currency_data`:
  - `id`: SERIAL PRIMARY KEY
  - `usd_to_cny`: DECIMAL(10,4)
  - `timestamp`: TIMESTAMP

## Error Handling

- Each task includes try-except blocks for error handling
- Download errors are logged but don't fail the DAG
- Parsing errors are logged but don't fail the DAG
- Database errors will cause the DAG to fail
