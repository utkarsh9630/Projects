SELECT
*
FROM {{ source('analytics', 'electricity_weather_historical') }}

