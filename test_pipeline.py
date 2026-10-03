# test_pipeline.py
import pandas as pd

from pipeline import SCHEMA, transform


def rohdaten(**aenderungen):
    zeile = {
        "bestell_id": "B-20260901-0001",
        "zeitpunkt": "2026-09-01 08:00:00",
        "kunde_id": "K1000",
        "produkt": "Crema Mild",
        "menge": "2",
        "einzelpreis": "11.50",
        "land": "DE",
        "quelldatei": "test.csv",
    }
    zeile.update(aenderungen)
    return pd.DataFrame([zeile])


def test_umsatz_wird_berechnet():
    gut, abgelehnt = transform(rohdaten())
    assert gut["umsatz"].iloc[0] == 23.0


def test_komma_im_preis_wird_zum_punkt():
    gut, abgelehnt = transform(rohdaten(einzelpreis="11,50"))
    assert gut["einzelpreis"].iloc[0] == 11.5


def test_land_wird_vereinheitlicht():
    gut, abgelehnt = transform(rohdaten(land="de "))
    assert gut["land"].iloc[0] == "DE"


def test_fehlende_menge_landet_in_der_quarantaene():
    gut, abgelehnt = transform(rohdaten(menge=None))
    assert len(gut) == 0
    assert abgelehnt["grund"].iloc[0] == "menge fehlt"


def test_dubletten_werden_entfernt():
    doppelt = pd.concat([rohdaten(), rohdaten()], ignore_index=True)
    gut, abgelehnt = transform(doppelt)
    assert len(gut) == 1


def test_ergebnis_passt_zum_schema():
    gut, abgelehnt = transform(rohdaten())
    SCHEMA.validate(gut)
