-- models/marts/dim_produkte.sql
{{ config(materialized='table') }}

select distinct
    sorte,
    kilopreis
from {{ ref('stg_bestellungen') }}
