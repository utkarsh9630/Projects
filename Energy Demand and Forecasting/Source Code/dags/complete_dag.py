from airflow import DAG
from airflow.models import Variable
from airflow.decorators import task
from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook
import pandas as pd

from datetime import timedelta
import datetime as dt
import requests
import logging

# Import dbt requirements
from pendulum import datetime
from airflow.operators.bash import BashOperator

# Establish connection to Snowflake database
def return_snowflake_conn():
    hook = SnowflakeHook(
        snowflake_conn_id='snowflake_conn'
    )
    conn = hook.get_conn()
    return conn.cursor()


#Fetch electricity data
@task
def fetch_electricity_data(start_date, end_date):
    api_key = Variable.get('electricity_api_key')

    # API URL and parameters
    url = 'https://api.eia.gov/v2/electricity/rto/daily-region-sub-ba-data/data/'

    params = {
        'api_key': api_key,
        'frequency': 'daily',
        'data[0]': 'value',
        'sort[0][column]': 'period',
        'sort[0][direction]': 'desc',
        'start': start_date,
        'end': end_date,
        'length': 10000,
        'facets[parent][]': 'CISO',
        'facets[timezone][]': 'Pacific'
    }

    # Fetch the data from the API
    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        if 'response' in data and 'data' in data['response']:
            df = pd.DataFrame(data['response']['data'])
            print(df.head())
            return df
        else:
            print("Data not found in the response.")
    else:
        print(f"Request failed with status code: {response.status_code}")
    return response


# Insert electricity data into Snowflake
@task
def load_electricity_data(cur, data, table_name):
    # Connect to Snowflake
    cur.execute("BEGIN;")

    # Create electricity data table
    create_electricity_table_query = f"""
    CREATE OR REPLACE TABLE {table_name}(
        period STRING,
        subba STRING,
        subba_name STRING,
        parent STRING,
        parent_name STRING,
        timezone STRING,
        value DOUBLE,
        value_units STRING,
        CONSTRAINT pk_electricity_data PRIMARY KEY (period, subba)
    );
    """
    cur.execute(create_electricity_table_query)

    # Fetch electricity data using the new function
    electricity_data = data

    # Batch insert electricity data
    electricity_data_to_insert = [
        (
            str(row['period']),
            str(row['subba']),
            str(row['subba-name']),
            str(row['parent']),
            str(row['parent-name']),
            str(row['timezone']),
            float(row['value']) if pd.notnull(row['value']) else None,  # Handle NaN
            str(row['value-units'])
        )
        for index, row in electricity_data.iterrows()
    ]
    insert_electricity_query = f"""
    INSERT INTO {table_name} (period, subba, subba_name, parent, parent_name, timezone, value, value_units)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    try:
        cur.executemany(insert_electricity_query, electricity_data_to_insert)
    except Exception as e:
        print("Error inserting electricity data:", e)

    # Commit and close the connection
    cur.execute("COMMIT;")
    

# Fetch historical weather data
@task
def fetch_historical_weather(start_date, latitude, longitude):
    """
    Fetch historical daily weather data for a specific location and date range.
    """
    today = dt.datetime.today().strftime('%Y-%m-%d')
    base_url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": today,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,snowfall_sum,windspeed_10m_max",
        "timezone": "America/Los_Angeles"  # Adjust timezone as needed
    }
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        data = response.json()
        if "daily" in data:
            daily_data = data["daily"]
            df = pd.DataFrame(daily_data)
            df.rename(columns={"time": "Date"}, inplace=True)
            df['avg_temperature'] = (df['temperature_2m_max'] + df['temperature_2m_min']) / 2
            return df
        else:
            raise ValueError("No 'daily' data found in the API response.")
    else:
        raise ValueError(f"Failed to fetch data. HTTP status code: {response.status_code}")

# Insert data directly into Snowflake using INSERT INTO
@task
def load_weather_data_to_snowflake(cur, df, table_name):
    
    cur.execute("BEGIN;")
    create_temperature_table_query = f"""
    CREATE OR REPLACE TABLE {table_name} (
    period DATE PRIMARY KEY,
    min_temperature FLOAT,
    max_temperature FLOAT,
    avg_temperature FLOAT,
    precipitation_sum FLOAT,
    snowfall_sum FLOAT,
    windspeed_10m_max FLOAT
    );
    """
    cur.execute(create_temperature_table_query)

    # Replace NaN with None
    df = df.applymap(lambda x: None if pd.isna(x) else x)
    

    # Prepare the SQL insert query
    insert_query = f"""
    INSERT INTO {table_name}
    (period, min_temperature, max_temperature, avg_temperature, precipitation_sum, snowfall_sum, windspeed_10m_max)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    
    # Prepare the data for insertion, ensuring correct types
    weather_data = []
    for _, row in df.iterrows():
        # Convert values to float and handle NaNs explicitly
        weather_data.append((
            row['Date'],
            float(row['temperature_2m_min']) if pd.notna(row['temperature_2m_min']) else None,
            float(row['temperature_2m_max']) if pd.notna(row['temperature_2m_max']) else None,
            float(row['avg_temperature']) if pd.notna(row['avg_temperature']) else None,
            float(row['precipitation_sum']) if pd.notna(row['precipitation_sum']) else None,
            float(row['snowfall_sum']) if pd.notna(row['snowfall_sum']) else None,
            float(row['windspeed_10m_max']) if pd.notna(row['windspeed_10m_max']) else None
        ))

    # Insert data
    try:
        #cursor.execute("BEGIN;")
        cur.executemany(insert_query, weather_data)
        print(f"Successfully inserted {len(weather_data)} rows.")
        cur.execute("COMMIT;")
    except Exception as e:
        cur.execute("ROLLBACK;")
        print("Error inserting data:", e)
        raise  # Re-raise exception to signal task failure


@task
def fetch_forecast_weather(start_date, latitude, longitude):
    """
    Fetch historical daily weather data for a specific location and date range.
    """
    today = dt.datetime.today().strftime('%Y-%m-%d')
    base_url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,snowfall_sum,windspeed_10m_max",
        "timezone": "America/Los_Angeles"  # Adjust timezone as needed
    }
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        data = response.json()
        if "daily" in data:
            daily_data = data["daily"]
            df = pd.DataFrame(daily_data)
            df.rename(columns={"time": "Date"}, inplace=True)
            df['avg_temperature'] = (df['temperature_2m_max'] + df['temperature_2m_min']) / 2
            return df
        else:
            raise ValueError("No 'daily' data found in the API response.")
    else:
        raise ValueError(f"Failed to fetch data. HTTP status code: {response.status_code}")


#Trains a forecasting model on electricity and weather data.
@task
def train(cur, train_input_table, train_view, forecast_function_name):
    """
     - Create a view with training related columns
     - Create a model with the view above
    """

    create_view_sql = f"""CREATE OR REPLACE VIEW {train_view} AS SELECT
    to_timestamp_ntz(PERIOD) as DATE,
    ELECTRICITY_VALUE_GWH,
    SUBBA,
    MIN_TEMPERATURE,
    MAX_TEMPERATURE,
    AVG_TEMPERATURE,
    PRECIPITATION_SUM,
    SNOWFALL_SUM,
    WINDSPEED_10M_MAX
    FROM {train_input_table}"""

    create_model_sql = f"""CREATE OR REPLACE SNOWFLAKE.ML.FORECAST {forecast_function_name}(
    INPUT_DATA => SYSTEM$REFERENCE('VIEW', '{train_view}'),
    SERIES_COLNAME => 'SUBBA',
    TIMESTAMP_COLNAME => 'DATE',
    TARGET_COLNAME => 'ELECTRICITY_VALUE_GWH',
    CONFIG_OBJECT => {{ 'ON_ERROR': 'SKIP' }}
    );"""

    try:
        logger = logging.getLogger(__name__)
        cur.execute(create_view_sql)
        logger.info("View created")
        cur.execute(create_model_sql)
        logger.info("Model for training created")
        # Inspect the accuracy metrics of your model. 
        cur.execute(f"CALL {forecast_function_name}!SHOW_EVALUATION_METRICS();")
        return True
    except Exception as e:
        print(e)
        raise

#Generates predictions based on the trained model.
@task
def predict(cur, forecast_function_name, forecast_input_table, forecast_table):
    """
     - Generate predictions and store the results to a table named forecast_table.
    """
    make_prediction_sql = f"""BEGIN
    -- This is the step that creates your predictions.
    CALL {forecast_function_name}!FORECAST(
        INPUT_DATA => SYSTEM$REFERENCE('Table', '{forecast_input_table}'),
        TIMESTAMP_COLNAME => 'period',
        SERIES_COLNAME => 'SUBBA',
        -- FORECASTING_PERIODS => 7,
        -- -- Here we set your prediction interval.
        CONFIG_OBJECT => {{'prediction_interval': 0.95}}
    );
    -- These steps store your predictions to a table.
    LET x := SQLID;
    CREATE OR REPLACE TABLE {forecast_table} AS SELECT * FROM TABLE(RESULT_SCAN(:x));
    END;"""
        

    try:
        logger = logging.getLogger(__name__)
        cur.execute(make_prediction_sql)
        logger.info("prediction created")
    except Exception as e:
        print(e)
        raise

DBT_PROJECT_DIR = "/opt/airflow/dbt"
DBT_VIZ_PROJECT_DIR = "/opt/airflow/dbt_viz"

with DAG(
    "complete-dag",
    start_date=datetime(2024, 11, 26),
    description="A sample Airflow DAG to invoke dbt runs using a BashOperator",
    schedule = '40 20 * * *',
    catchup=False,
    default_args={
        "env": {
            "DBT_USER": "{{ conn.snowflake_conn.login }}",
            "DBT_PASSWORD": "{{ conn.snowflake_conn.password }}",
            "DBT_ACCOUNT": "{{ conn.snowflake_conn.extra_dejson.account }}",
            "DBT_SCHEMA": "{{ conn.snowflake_conn.schema }}",
            "DBT_DATABASE": "{{ conn.snowflake_conn.extra_dejson.database }}",
            "DBT_ROLE": "{{ conn.snowflake_conn.extra_dejson.role }}",
            "DBT_WAREHOUSE": "{{ conn.snowflake_conn.extra_dejson.warehouse }}",
            "DBT_TYPE": "snowflake"
        }
    },
    ) as dag:

    cur = return_snowflake_conn()
    today = dt.datetime.today().strftime('%Y-%m-%d')
    start_date = "2022-01-01"
    end_date = today
    
    
    
    

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=f"/home/airflow/.local/bin/dbt run --profiles-dir {DBT_PROJECT_DIR} --project-dir {DBT_PROJECT_DIR}",
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"/home/airflow/.local/bin/dbt test --profiles-dir {DBT_PROJECT_DIR} --project-dir {DBT_PROJECT_DIR}",
    )

    dbt_snapshot = BashOperator(
        task_id="dbt_snapshot",
        bash_command=f"/home/airflow/.local/bin/dbt snapshot --profiles-dir {DBT_PROJECT_DIR} --project-dir {DBT_PROJECT_DIR}",
    )

    dbt_run_2 = BashOperator(
        task_id="dbt_run_2",
        bash_command=f"/home/airflow/.local/bin/dbt run --profiles-dir {DBT_VIZ_PROJECT_DIR} --project-dir {DBT_VIZ_PROJECT_DIR}",
    )

    dbt_test_2 = BashOperator(
        task_id="dbt_test_2",
        bash_command=f"/home/airflow/.local/bin/dbt test --profiles-dir {DBT_VIZ_PROJECT_DIR} --project-dir {DBT_VIZ_PROJECT_DIR}",
    )

    dbt_snapshot_2 = BashOperator(
        task_id="dbt_snapshot_2",
        bash_command=f"/home/airflow/.local/bin/dbt snapshot --profiles-dir {DBT_VIZ_PROJECT_DIR} --project-dir {DBT_VIZ_PROJECT_DIR}",
    )

    start_date = "2022-01-01"
    latitude = 36.7783  # Example latitude (California)
    longitude = 119.4179  # Example longitude (California)
    historical_weather_table = "dev.raw_data.weather_data_historical"
    weather_forecast_table = "dev.raw_data.weather_data_forecast"
    raw_electricity_table = "dev.raw_data.electricity_data_historical"

    train_input_table = "dev.analytics.electricity_weather_historical"
    train_view = "dev.analytics.train_view"
    
    predict_input_table = "dev.analytics.weather_forecast_processed"
    forecast_table = "dev.analytics.electricity_data_forecast"
    forecast_function_name = "dev.analytics.energy_usage"
    



    # Dependency setup
    

    data = fetch_electricity_data(start_date, end_date) 
    load_electricity_data(cur, data, raw_electricity_table) >> dbt_run

    weather_data = fetch_historical_weather(start_date, latitude, longitude)
    load_weather_data_to_snowflake(cur, weather_data, historical_weather_table) >> dbt_run
    
    
    
    
    forecast_weather_data = fetch_forecast_weather(start_date, latitude, longitude)
    load_weather_data_to_snowflake(cur, forecast_weather_data, weather_forecast_table) >> dbt_run


    dbt_run >> dbt_test >> dbt_snapshot
    dbt_snapshot >> train(cur, train_input_table, train_view, forecast_function_name) \
        >> predict(cur, forecast_function_name, predict_input_table, forecast_table) \
            >> dbt_run_2
    
    dbt_run_2 >> dbt_test_2 >> dbt_snapshot_2



