# umsatz_je_tag.py
import duckdb

con = duckdb.connect("bohnenwerk.duckdb", read_only=True)
con.sql("""
    SELECT CAST(zeitpunkt AS DATE) AS tag,
           count(*)                AS bestellungen,
           sum(umsatz)             AS umsatz
    FROM bestellungen
    GROUP BY tag
    ORDER BY tag
""").show()
gesamt = con.execute("SELECT sum(umsatz) FROM bestellungen").fetchone()[0]
print(f"Umsatz der Woche: {gesamt} Euro")
con.close()
