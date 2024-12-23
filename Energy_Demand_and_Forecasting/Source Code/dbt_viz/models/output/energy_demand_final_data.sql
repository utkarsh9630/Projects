select * ,
       -- Temperature categories
        CASE 
            WHEN AVG_TEMPERATURE < 0 THEN 'Cold'
            WHEN AVG_TEMPERATURE BETWEEN 0 AND 15 THEN 'Cool'
            WHEN AVG_TEMPERATURE > 15 THEN 'Warm'
            ELSE 'Unknown'
        END AS temperature_category,
        
        -- Wind speed categories
        CASE 
            WHEN WINDSPEED_10M_MAX > 20 THEN 'High Wind'
            WHEN WINDSPEED_10M_MAX BETWEEN 10 AND 20 THEN 'Moderate Wind'
            ELSE 'Low Wind'
        END AS wind_category,

        -- Extreme weather day flag
        CASE
            WHEN PRECIPITATION_SUM > 50 OR SNOWFALL_SUM > 10 OR WINDSPEED_10M_MAX > 25 THEN 1
            ELSE 0
        END AS is_extreme_weather_day,

        -- Predicted or actual
        case when upper_bound is null then 'Actual' else 'Predicted' end as actual_predicted_flag
    from {{ ref('energy_historical_forecast_data') }}

