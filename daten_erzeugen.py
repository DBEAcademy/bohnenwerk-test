# daten_erzeugen.py
# Erzeugt sieben Tagesdateien mit Bestellungen der Kaffeeroesterei Bohnenwerk.
# Der Zufall ist fest eingestellt, damit alle dieselben Daten bekommen.
import csv
import random
from datetime import date, datetime, timedelta
from pathlib import Path

random.seed(42)

PRODUKTE = {
    "Espresso Classico": 12.90,
    "Crema Mild": 11.50,
    "Hochland Filter": 13.40,
    "Entkoffeiniert": 12.20,
    "Kenia AA": 16.80,
    "Hausmischung": 9.90,
}
LAENDER = ["DE", "DE", "DE", "DE", "AT", "CH"]

ordner = Path("eingang")
ordner.mkdir(exist_ok=True)

start = date(2026, 9, 1)
for tag in range(7):
    datum = start + timedelta(days=tag)
    zeilen = []
    for nummer in range(1, 201):
        produkt = random.choice(list(PRODUKTE))
        zeitpunkt = datetime(datum.year, datum.month, datum.day) + timedelta(
            seconds=random.randint(6 * 3600, 22 * 3600)
        )
        zeile = {
            "bestell_id": f"B-{datum:%Y%m%d}-{nummer:04d}",
            "zeitpunkt": f"{zeitpunkt:%Y-%m-%d %H:%M:%S}",
            "kunde_id": f"K{random.randint(1000, 1400)}",
            "produkt": produkt,
            "menge": str(random.randint(1, 5)),
            "einzelpreis": f"{PRODUKTE[produkt]:.2f}",
            "land": random.choice(LAENDER),
        }
        # Absichtlich eingebaute Fehler, wie sie in echten Lieferungen vorkommen
        zufall = random.random()
        if zufall < 0.03:
            zeile["menge"] = ""
        elif zufall < 0.06:
            zeile["einzelpreis"] = zeile["einzelpreis"].replace(".", ",")
        elif zufall < 0.09:
            zeile["land"] = zeile["land"].lower() + " "
        elif zufall < 0.10:
            zeile["menge"] = "-" + zeile["menge"]
        zeilen.append(zeile)
    # Ein paar Bestellungen kommen doppelt in der Datei an
    zeilen += random.sample(zeilen, 4)
    datei = ordner / f"bestellungen_{datum:%Y-%m-%d}.csv"
    with open(datei, "w", newline="", encoding="utf-8") as f:
        schreiber = csv.DictWriter(f, fieldnames=list(zeilen[0]))
        schreiber.writeheader()
        schreiber.writerows(zeilen)
    print(f"{datei} geschrieben ({len(zeilen)} Zeilen)")
