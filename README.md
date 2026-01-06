# Intelligent Energy Demand Forecasting in the US

A comprehensive data engineering and machine learning pipeline for forecasting electricity consumption in California using real-time weather data and historical energy patterns.

## Project Overview

## Project Overview

This project analyzes electricity consumption patterns in California by integrating data from the U.S. Energy Information Administration (EIA) with weather data from OpenMeteo API. We built an end-to-end data pipeline that collects, processes, and analyzes energy consumption data to forecast usage for the next 7 days. The system uses Apache Airflow for workflow orchestration, Snowflake as a cloud data warehouse, dbt for data transformations, and Snowflake's machine learning capabilities for predictive modeling.

### What This Project Does

- Automatically collects electricity and weather data through APIs
- Processes and transforms data using modern data engineering tools
- Trains a machine learning model to predict energy consumption
- Provides insights through interactive Power BI dashboards
- Runs daily to keep predictions up-to-date

## Architecture

```
┌─────────────┐     ┌──────────────┐
│   EIA API   │     │ OpenMeteo API│
│ (Electricity)│     │   (Weather)  │
└──────┬──────┘     └──────┬───────┘
       │                   │
       └───────┬───────────┘
               │ Apache Airflow
               ▼
       ┌───────────────┐
       │   Snowflake   │
       │ Data Warehouse│
       └───────┬───────┘
               │ dbt Transformations
               ▼
       ┌───────────────┐
       │  Snowflake ML │
       │   Forecasting │
       └───────┬───────┘
               │
               ▼
       ┌───────────────┐
       │   Power BI    │
       │  Dashboards   │
       └───────────────┘
```

## Project Structure

```
Energy_Demand_and_Forecasting/
├── Documentation/
│   ├── Group6_Project_Presentation.pptx
│   ├── group_project.pdf
│   ├── Project_Proposal_Group6.pdf
│   └── Project thumbnail.png
│
└── Source Code/
    ├── dags/
    │   └── complete_dag.py              # Main Airflow DAG
    ├── dbt/
    │   ├── models/
    │   │   ├── input/                   # Source data models
    │   │   └── output/                  # Transformed data models
    │   ├── snapshots/                   # dbt snapshots
    │   ├── tests/                       # Data quality tests
    │   └── dbt_project.yml
    ├── dbt_viz/                         # Visualization-specific dbt models
    ├── config/                          # Configuration files
    ├── docker-compose.yaml              # Docker orchestration
    └── DATA226 GP- Group6.pbix         # Power BI dashboard
```

## Technology Stack

### Data Infrastructure
- **Apache Airflow**: Workflow orchestration and scheduling
- **Docker**: Containerization for reproducible environments
- **Snowflake**: Cloud data warehouse for storage and compute

### Data Processing
- **dbt (Data Build Tool)**: Data transformation and modeling
- **Python**: Data extraction and preprocessing
- **Pandas**: Data manipulation

### Machine Learning
- **Snowflake ML**: Built-in forecasting capabilities
- **Time Series Forecasting**: 7-day ahead predictions

### Visualization
- **Power BI**: Interactive dashboards and reporting

### APIs
- **EIA API**: U.S. Energy Information Administration electricity data
- **OpenMeteo API**: Historical and forecast weather data

## Data Sources

### 1. Electricity Consumption Data (EIA)
- **Source**: U.S. Energy Information Administration API
- **Frequency**: Daily
- **Coverage**: California utility companies (PG&E, SCE, SDGE, etc.)
- **Features**:
  - Period (Date)
  - SubBA (Utility company code)
  - SubBA Name (Full company name)
  - Parent Organization (CISO)
  - Timezone
  - Energy Value (MWh)

### 2. Weather Data (OpenMeteo)
- **Source**: OpenMeteo Archive & Forecast APIs
- **Location**: California (Lat: 36.7783, Lon: 119.4179)
- **Features**:
  - Temperature (Min/Max/Avg) - °C
  - Precipitation - mm
  - Snowfall - mm
  - Wind Speed - m/s

## Getting Started

### Prerequisites

```bash
# Required software
- Docker & Docker Compose
- Python 3.9+
- Snowflake account
- Power BI Desktop (for dashboards)
```

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/utkarsh9630/Projects.git
cd Projects/Energy_Demand_and_Forecasting/Source\ Code
```

2. **Set up environment variables**
```bash
# Create a .env file with the following:
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_USER=your_user
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_DATABASE=your_database
SNOWFLAKE_SCHEMA=your_schema
SNOWFLAKE_WAREHOUSE=your_warehouse
EIA_API_KEY=your_eia_api_key
```

3. **Initialize Airflow**
```bash
docker compose up airflow-init
```

4. **Start the services**
```bash
docker compose up
```

5. **Access Airflow UI**
- Navigate to `http://localhost:8080`
- Login with credentials: `airflow` / `airflow`

### Configuration

1. **Snowflake Connection**:
   - In Airflow UI, configure the `snowflake_conn` connection with your credentials

2. **API Keys**:
   - Add your EIA API key as an Airflow variable: `electricity_api_key`

## Pipeline Workflow

### 1. Data Extraction (Airflow Tasks)
- `fetch_electricity_data`: Retrieves daily electricity consumption from EIA API
- `fetch_historical_weather`: Fetches historical weather data from OpenMeteo
- `fetch_forecast_weather`: Retrieves 7-day weather forecasts

### 2. Data Loading
- `load_electricity_data`: Inserts electricity data into Snowflake raw tables
- `load_weather_data_to_snowflake`: Loads weather data (historical and forecast)

### 3. Data Transformation (dbt)
- **Input Models**: Clean and standardize raw data
- **Output Models**: 
  - `electricity_weather_historical`: Merged historical data with weather features
  - `weather_forecast_processed`: Prepared forecast data with utility mapping
  - Energy value conversion from MWh to GWh

### 4. Machine Learning
- **Training**: Uses `electricity_weather_historical` table
- **Model**: Snowflake ML Forecasting with time series analysis
- **Features**: Weather variables as exogenous inputs
- **Target**: Electricity consumption (GWh)
- **Prediction Horizon**: 7 days

### 5. Post-Processing (dbt)
- Merges historical and forecast data
- Calculates derived metrics:
  - Temperature categories
  - Wind speed categories
  - Extreme weather indicators
  - Predicted/Actual flags

### 6. Data Quality
- **dbt Tests**: Null value checks, data integrity validation
- **Snapshots**: Change tracking using check strategy on period and consumption values

## Data Models

### Key Tables in Snowflake

| Schema | Table | Description |
|--------|-------|-------------|
| `raw_data` | `electricity_data_historical` | Raw electricity consumption data |
| `raw_data` | `weather_data_historical` | Historical weather measurements |
| `raw_data` | `weather_data_forecast` | 7-day weather forecasts |
| `analytics` | `electricity_weather_historical` | Merged historical data for training |
| `analytics` | `weather_forecast_processed` | Prepared forecast data with utilities |
| `analytics` | `electricity_data_forecast` | ML-generated consumption predictions |
| `analytics` | `energy_demand_final_data` | Final dataset with all metrics |

## Machine Learning Model Details

### Snowflake ML Forecast
- **Algorithm**: Automated time series forecasting
- **Series Column**: `SUBBA` (utility company)
- **Timestamp Column**: `PERIOD` (date)
- **Target**: `ELECTRICITY_VALUE_GWH`
- **Exogenous Variables**: 
  - MIN_TEMPERATURE
  - MAX_TEMPERATURE
  - AVG_TEMPERATURE
  - PRECIPITATION_SUM
  - SNOWFALL_SUM
  - WINDSPEED_10M_MAX

### Model Configuration
```python
SNOWFLAKE.ML.FORECAST(
    INPUT_DATA => electricity_weather_historical,
    SERIES_COLNAME => 'SUBBA',
    TIMESTAMP_COLNAME => 'DATE',
    TARGET_COLNAME => 'ELECTRICITY_VALUE_GWH',
    CONFIG_OBJECT => {'prediction_interval': 0.95}
)
```

## Dashboard Insights

Our Power BI dashboard shows:
- How much electricity each utility company uses over time
- How weather conditions (temperature, rain, wind) affect energy consumption
- Comparisons between 2022, 2023, and 2024 to see yearly trends
- The 7-day forecast with predicted consumption values
- Highlighting when unusual weather events happen and how they impact usage

## DAG Execution Flow

```
fetch_electricity_data ──┐
                         ├─► dbt_run ──► dbt_test ──► dbt_snapshot ──► train ──► predict ──► dbt_run_2 ──► dbt_test_2 ──► dbt_snapshot_2
fetch_historical_weather ┤
                         │
fetch_forecast_weather ──┘
```

**Schedule**: Daily at 20:40 UTC (`40 20 * * *`)

## Testing

dbt tests ensure data quality:
- Not-null constraints on critical columns
- Unique key validation
- Data freshness checks
- Referential integrity

Run tests manually:
```bash
dbt test --profiles-dir /opt/airflow/dbt --project-dir /opt/airflow/dbt
```

## Key Findings

From our analysis, we observed several interesting patterns:

1. Temperature has a strong correlation with energy consumption. When it gets really hot or really cold, people use more electricity for heating and cooling.

2. California has mild winters compared to other states, so we see higher consumption during summer months due to air conditioning use.

3. Different utility companies show different consumption patterns, which makes sense given the regional differences across California.

4. Our forecasting model does a decent job predicting consumption 7 days out, which could be useful for utility companies planning their energy supply.

## Contributors

- **Aishanee Sinha**
- **Ketki Ramakant Maddiwar**
- **Leela Prasad Dammalapati**
- **Utkarsh Tripathi**

## Documentation

Additional documentation available in the `/Documentation` folder:
- Project proposal with objectives and methodology
- Detailed project report with analysis
- PowerPoint presentation with visualizations
- Architecture diagrams

## Data Privacy and Security

- All API credentials stored securely in Airflow Variables
- Snowflake connections encrypted
- No PII (Personally Identifiable Information) collected
- Data aggregated at utility company level

## Future Enhancements

Some ideas we had for extending this project:

- Adding real-time streaming data instead of daily batch processing
- Testing other ML models like LSTM or Prophet to compare accuracy
- Building anomaly detection to identify unusual consumption patterns
- Including data from solar and wind energy sources
- Expanding to other states beyond California
- Creating a mobile app version of the dashboard

## License

This project is part of an academic course project. Please contact the contributors for usage permissions.

## Contact

For questions or collaboration:
- GitHub: [@utkarsh9630](https://github.com/utkarsh9630)

---

This project was developed as part of a data engineering course to demonstrate end-to-end pipeline development and machine learning integration.
