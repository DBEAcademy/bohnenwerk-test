-- models/marts/fct_bestellungen.sql
{{ config(materialized='table') }}

select
    bestell_id,
    bestell_datum,
    wochentag,
    sorte,
    land,
    menge,
    umsatz
from {{ ref('stg_bestellungen') }}
