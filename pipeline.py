# pipeline.py
import logging
import os
from pathlib import Path

import duckdb
import pandas as pd
import pandera.pandas as pa

EINGANG = Path(os.environ.get("BOHNENWERK_EINGANG", "eingang"))
DATENBANK = os.environ.get("BOHNENWERK_DATENBANK", "bohnenwerk.duckdb")
LOGDATEI = os.environ.get("BOHNENWERK_LOGDATEI", "pipeline.log")
LAENDER = ["DE", "AT", "CH"]

log = logging.getLogger("pipeline")

SCHEMA = pa.DataFrameSchema(
    {
        "bestell_id": pa.Column(str, pa.Check.str_matches(r"^B-\d{8}-\d{4}$"), unique=True),
        "zeitpunkt": pa.Column("datetime64[ns]"),
        "kunde_id": pa.Column(str, pa.Check.str_matches(r"^K\d{4}$")),
        "produkt": pa.Column(str),
        "menge": pa.Column(int, pa.Check.in_range(1, 50)),
        "einzelpreis": pa.Column(float, pa.Check.in_range(1, 100)),
        "land": pa.Column(str, pa.Check.isin(LAENDER)),
        "quelldatei": pa.Column(str),
        "umsatz": pa.Column(float, pa.Check.ge(0)),
    }
)


def logging_einrichten():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler(LOGDATEI, encoding="utf-8")],
    )


def tabellen_anlegen(con):
    con.execute("""
        CREATE TABLE IF NOT EXISTS bestellungen (
            bestell_id  VARCHAR PRIMARY KEY,
            zeitpunkt   TIMESTAMP,
            kunde_id    VARCHAR,
            produkt     VARCHAR,
            menge       INTEGER,
            einzelpreis DECIMAL(8, 2),
            land        VARCHAR,
            quelldatei  VARCHAR,
            umsatz      DECIMAL(10, 2)
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS geladene_dateien (
            dateiname  VARCHAR PRIMARY KEY,
            geladen_am TIMESTAMP DEFAULT current_timestamp,
            zeilen     INTEGER
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS quarantaene (
            bestell_id  VARCHAR,
            zeitpunkt   VARCHAR,
            kunde_id    VARCHAR,
            produkt     VARCHAR,
            menge       VARCHAR,
            einzelpreis VARCHAR,
            land        VARCHAR,
            quelldatei  VARCHAR,
            grund       VARCHAR
        )
    """)


def neue_dateien(con):
    bekannt = {zeile[0] for zeile in con.execute("SELECT dateiname FROM geladene_dateien").fetchall()}
    return [datei for datei in sorted(EINGANG.glob("bestellungen_*.csv")) if datei.name not in bekannt]


def extract(dateien):
    teile = []
    for datei in dateien:
        df = pd.read_csv(datei, dtype=str)
        df["quelldatei"] = datei.name
        log.info("%s gelesen: %d Zeilen", datei.name, len(df))
        teile.append(df)
    return pd.concat(teile, ignore_index=True)


def transform(df):
    vorher = len(df)
    df = df.drop_duplicates(subset="bestell_id").copy()
    log.info("%d Dubletten entfernt", vorher - len(df))
    df["land"] = df["land"].str.strip().str.upper()
    menge = pd.to_numeric(df["menge"], errors="coerce")
    df["grund"] = None
    df.loc[menge.isna(), "grund"] = "menge fehlt"
    df.loc[menge <= 0, "grund"] = "menge nicht positiv"
    df.loc[~df["land"].isin(LAENDER), "grund"] = "unbekanntes land"
    abgelehnt = df[df["grund"].notna()].copy()
    gut = df[df["grund"].isna()].drop(columns="grund")
    gut["zeitpunkt"] = pd.to_datetime(gut["zeitpunkt"])
    gut["menge"] = gut["menge"].astype(int)
    gut["einzelpreis"] = gut["einzelpreis"].astype(float)
    gut["umsatz"] = (gut["menge"] * gut["einzelpreis"]).round(2)
    if len(abgelehnt) > 0:
        log.warning("%d Zeilen in die Quarantäne verschoben", len(abgelehnt))
    return gut, abgelehnt


def load(con, gut, abgelehnt):
    con.execute("INSERT OR REPLACE INTO bestellungen SELECT * FROM gut")
    con.execute("INSERT INTO quarantaene SELECT * FROM abgelehnt")
    for dateiname, zeilen in gut.groupby("quelldatei").size().items():
        con.execute(
            "INSERT INTO geladene_dateien (dateiname, zeilen) VALUES (?, ?)",
            [dateiname, int(zeilen)],
        )
    log.info("%d Bestellungen geladen", len(gut))


def main():
    logging_einrichten()
    log.info("Pipeline startet: Eingang %s, Datenbank %s", EINGANG, DATENBANK)
    con = duckdb.connect(DATENBANK)
    tabellen_anlegen(con)
    dateien = neue_dateien(con)
    if not dateien:
        log.info("Keine neuen Dateien, nichts zu tun")
    else:
        gut, abgelehnt = transform(extract(dateien))
        SCHEMA.validate(gut)
        load(con, gut, abgelehnt)
    con.close()
    log.info("Pipeline fertig")


if __name__ == "__main__":
    main()
