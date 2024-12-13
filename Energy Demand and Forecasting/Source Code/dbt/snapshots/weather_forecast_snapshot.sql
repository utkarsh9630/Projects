{% snapshot weather_forecast_snapshot %}

{{
  config(
    target_schema='snapshot',
    unique_key='unique_id',
    strategy='check',
    check_cols=['period'],
    invalidate_hard_deletes=True
  )
}}

SELECT * FROM {{ ref('weather_forecast_processed') }}

{% endsnapshot %}


