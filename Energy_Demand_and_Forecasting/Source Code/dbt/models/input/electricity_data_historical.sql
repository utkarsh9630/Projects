SELECT
    PERIOD,
    SUBBA,
    SUBBA_NAME,
    PARENT,
    PARENT_NAME,
    TIMEZONE,
    VALUE AS electricity_value,
    VALUE_UNITS
FROM {{ source('raw_data', 'electricity_data_historical') }}

