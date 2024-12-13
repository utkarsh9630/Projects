    with temp as (SELECT period,
    ELECTRICITY_VALUE_GWH,
    SUBBA,
    MIN_TEMPERATURE,
    MAX_TEMPERATURE,
    AVG_TEMPERATURE,
    PRECIPITATION_SUM,
    SNOWFALL_SUM,
    WINDSPEED_10M_MAX, NULL AS lower_bound, NULL AS upper_bound
    FROM {{ref('electricity_weather_historical')}}
    UNION
    select 
    period,
    ELECTRICITY_VALUE_GWH,
    subba,
    MIN_TEMPERATURE,
    MAX_TEMPERATURE,
    AVG_TEMPERATURE,
    PRECIPITATION_SUM,
    SNOWFALL_SUM,
    WINDSPEED_10M_MAX, lower_bound, upper_bound
    FROM {{ref('electricity_weather_forecast')}}
    order by period desc)
    select *, concat(period,subba) as unique_id
    from temp