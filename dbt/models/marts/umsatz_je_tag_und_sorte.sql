-- models/marts/umsatz_je_tag_und_sorte.sql
{{ config(materialized='table') }}

select
    bestell_datum,
    sorte,
    count(*) as bestellungen,
    sum(menge) as verkaufte_kg,
    sum(umsatz) as umsatz
from {{ ref('fct_bestellungen') }}
group by bestell_datum, sorte
order by bestell_datum, sorte
