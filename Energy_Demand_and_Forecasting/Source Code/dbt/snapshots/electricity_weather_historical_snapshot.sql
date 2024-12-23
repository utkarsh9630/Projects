{% snapshot electricity_weather_historical_snapshot %}

{{
  config(
    target_schema='snapshot',
    unique_key='unique_id',
    strategy='check',
    check_cols=['period','ELECTRICITY_VALUE_GWH'],
    invalidate_hard_deletes=True
  )
}}

SELECT * FROM {{ ref('electricity_weather_historical') }}

{% endsnapshot %}



