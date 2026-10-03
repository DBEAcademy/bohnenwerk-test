-- models/staging/stg_bestellungen.sql
select
    bestell_id,
    kunde_id,
    cast(zeitpunkt as date) as bestell_datum,
    dayname(zeitpunkt) as wochentag,
    produkt as sorte,
    menge,
    einzelpreis as kilopreis,
    umsatz,
    land
from {{ source('pipeline', 'bestellungen') }}
