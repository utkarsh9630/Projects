select a.*, b.*,concat(PERIOD,SUBBA) as unique_id  from {{ref('weather_data_forecast')}} a cross join 
(SELECT distinct subba FROM {{ ref('electricity_data_historical')}}) b
order by period
