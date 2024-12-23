SELECT * FROM {{ source('raw_data', 'weather_data_historical') }}

-- SELECT
--     PERIOD,
--     AVG_TEMPERATURE,
--     PRECIPITATION_SUM,
--     SNOWFALL_SUM,
--     WINDSPEED_10M_MAX
-- FROM {{ source('raw_data', 'weather_data_historical') }}
