-- tests/umsatz_nicht_negativ.sql
select *
from {{ ref('fct_bestellungen') }}
where umsatz < 0
