# Airflow Data Pipeline with Docker

This project implements a containerized Airflow DAG that scrapes weather and currency exchange rate data from XML feeds and stores the results in a PostgreSQL database.

## 🚀 Features

- **Containerized** with Docker and Docker Compose
- **Data Collection**:
  - 🌡️ Weather data from `https://forecast.weather.gov/xml/current_obs/KJFK.xml`
  - 💱 Currency exchange rates from `https://www.floatrates.com/daily/usd.xml`
- **Data Processing**:
  - Current temperature in New York (converted to Celsius)
  - USD to CNY exchange rate extraction
- **Data Storage**: PostgreSQL database with proper schema
- **Error Handling**: Comprehensive logging and error handling
- **Scheduling**: Configurable schedule (default: hourly)

## 🛠️ Project Structure

```
.
├── dags/                    # Airflow DAG definitions
│   └── scraping_dag.py      # Main DAG file
├── plugins/                 # Custom Airflow plugins
│   └── helpers/
│       ├── __init__.py
│       └── data_processing.py  # Core data processing logic
├── .env                     # Environment variables
├── .gitattributes           # Git configuration
├── .gitignore              # Git ignore rules
├── docker-compose.yml       # Docker Compose configuration
├── Dockerfile              # Custom Airflow image
├── README.md               # This file
└── setup.py                # Python package configuration
```

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose installed
- At least 4GB of free memory for the containers

### Running the Project

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd scraper
   ```

2. **Start the services**
   ```bash
   docker-compose up -d
   ```

3. **Access Airflow UI**
   - Open http://localhost:8080 in your browser
   - Default credentials: `airflow` / `airflow`

4. **Trigger the DAG**
   - In the Airflow UI, find the `scraping_dag`
   - Toggle the DAG to activate it
   - Trigger a manual run using the play button

## 📊 Database Schema

The data is stored in two PostgreSQL tables:

### `weather_data`
- `id`: SERIAL PRIMARY KEY
- `temperature_c`: DECIMAL(5,2)
- `timestamp`: TIMESTAMP

### `currency_data`
- `id`: SERIAL PRIMARY KEY
- `usd_to_cny`: DECIMAL(10,4)
- `timestamp`: TIMESTAMP

## 🔧 Customization

### Environment Variables
Edit the `.env` file to configure:
- Database credentials
- Airflow settings
- Data sources and destinations

### DAG Configuration
Modify `dags/scraping_dag.py` to:
- Change the schedule interval
- Adjust task parameters
- Add new data sources

## 🐛 Troubleshooting

### Common Issues

1. **Port conflicts**
   - Ensure ports 8080 (Airflow) and 5432 (PostgreSQL) are available

2. **Container startup issues**
   - Check logs: `docker-compose logs -f`
   - Ensure Docker has enough resources (4GB+ RAM recommended)

3. **DAG not appearing**
   - Check the `dags` volume mount in `docker-compose.yml`
   - Verify file permissions in the `dags` directory

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
