WITH electricity AS (
    SELECT *
    FROM {{ ref('electricity_data_historical') }}
),

weather AS (
    SELECT *
    FROM {{ ref('weather_data_historical') }}
)

SELECT
    e.PERIOD,
    e.SUBBA,
    e.SUBBA_NAME,
    e.PARENT,
    e.PARENT_NAME,
    e.TIMEZONE,
    -- Convert energy to GWh
    e.electricity_value / 1000 AS electricity_value_gwh,
    w.MIN_TEMPERATURE,
    w.MAX_TEMPERATURE,
    w.AVG_TEMPERATURE,
    w.PRECIPITATION_SUM,
    w.SNOWFALL_SUM,
    w.WINDSPEED_10M_MAX,
    concat(e.PERIOD,e.SUBBA) as unique_id 
FROM electricity e
LEFT JOIN weather w
ON e.PERIOD = w.PERIOD
