# dags/bohnenwerk.py
from datetime import datetime, timedelta

import duckdb
from airflow.sdk import CronDataIntervalTimetable, dag, task

import pipeline


@dag(
    dag_id="bohnenwerk_pipeline",
    schedule=CronDataIntervalTimetable("@daily", timezone="UTC"),
    start_date=datetime(2026, 9, 1),
    catchup=False,
    max_active_runs=1,
    default_args={
        "retries": 2,
        "retry_delay": timedelta(minutes=2),
    },
)
def bohnenwerk_pipeline():

    @task
    def datei_des_tages(logical_date=None):
        if logical_date is None:
            raise ValueError("Dieser Lauf hat kein logisches Datum, starte ihn mit Datum")
        dateiname = f"bestellungen_{logical_date:%Y-%m-%d}.csv"
        if not (pipeline.EINGANG / dateiname).exists():
            raise FileNotFoundError(f"{dateiname} ist noch nicht im Eingang")
        with duckdb.connect(pipeline.DATENBANK) as con:
            pipeline.tabellen_anlegen(con)
            neu = [datei.name for datei in pipeline.neue_dateien(con)]
        if dateiname not in neu:
            pipeline.log.info("%s ist schon geladen", dateiname)
            return []
        return [dateiname]

    @task
    def laden(dateinamen):
        with duckdb.connect(pipeline.DATENBANK) as con:
            dateien = [datei for datei in pipeline.neue_dateien(con) if datei.name in dateinamen]
            if not dateien:
                pipeline.log.info("Keine neuen Dateien, nichts zu tun")
                return 0
            gut, abgelehnt = pipeline.transform(pipeline.extract(dateien))
            pipeline.SCHEMA.validate(gut)
            pipeline.load(con, gut, abgelehnt)
        return len(gut)

    @task.bash
    def auswerten():
        return "cd /bohnenwerk/dbt && dbt build"

    @task
    def bericht():
        with duckdb.connect(pipeline.DATENBANK, read_only=True) as con:
            bestellungen = con.execute("SELECT count(*) FROM bestellungen").fetchone()[0]
            quarantaene = con.execute("SELECT count(*) FROM quarantaene").fetchone()[0]
        pipeline.log.info("In der Datenbank: %d Bestellungen, %d Zeilen in der Quarantäne", bestellungen, quarantaene)

    laden(datei_des_tages()) >> auswerten() >> bericht()


bohnenwerk_pipeline()
