select a.forecast as ELECTRICITY_VALUE_GWH,a.lower_bound,a.upper_bound, b.* 
from {{source('analytics', 'electricity_data_forecast')}} 
    a left join {{source('analytics', 'weather_forecast_processed')}} b on 
    replace(a.series, '"', '')= b.subba and left(a.ts,10) = b.PERIOD

