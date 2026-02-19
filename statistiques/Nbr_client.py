import matplotlib.pyplot as plt
import sqlite3
import pandas as pd

def nbr_client():

    conn = sqlite3.connect("DB/dataset3.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    min_date, a, b = cur.execute("SELECT MIN(date_creation), MAX(date_fin), MAX(date_creation) FROM projet ").fetchone()
    max_date = max(a, b)
    if not min_date or not max_date:
        conn.close()
        return  

    cur.execute("""
    SELECT strftime('%Y-%m', date_creation) AS month, COUNT(*) AS count
    FROM projet
    WHERE date_creation BETWEEN ? AND ?
    GROUP BY month
    ORDER BY month;
    """, (min_date, max_date))
    rows = cur.fetchall()
    comptes= {r[0]: r[1] for r in rows}

    dates = pd.date_range(start= min_date, end=max_date, freq='MS')
    abs = [d.strftime('%Y-%m') for d in dates]
    ord = []
    for d in abs :
        if d in comptes:
            ord.append(comptes[d])
        else:
            ord.append(0)

    plt.figure()
    plt.plot(abs, ord)
    plt.xlabel("Mois")
    plt.ylabel("Nombre de clients")
    plt.title(f"Nombre de clients entre {min_date} et {max_date}")
    plt.tight_layout()
    plt.show()

    conn.close()
nbr_client()

