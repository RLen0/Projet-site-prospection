import sqlite3
import matplotlib.pyplot as plt
import pandas as pd 

def projets_en_cours():
    conn = sqlite3.connect("database3.db")
    cur = conn.cursor()


    min_date, max_date = cur.execute("SELECT MIN(date_creation), MAX(date_creation) FROM projet").fetchone()
    
    if not min_date or not max_date:
        conn.close()
        return  

   
    rows = cur.execute("""
        SELECT strftime('%Y-%m', date_creation) AS month, COUNT(*) 
        FROM projet
        WHERE status = 'en cours'
        GROUP BY month
        ORDER BY month
    """).fetchall()
    comptes= {r[0]: r[1] for r in rows}

    dates = pd.date_range(start= min_date, end=max_date, freq='MS')
    abs = [d.strftime('%Y-%m') for d in dates]
    ord = []
    for d in abs :
        if d in comptes:
            ord.append(comptes[d])
        else:
            ord.append(0)

    
    plt.figure(figsize=(10, 4))
    plt.plot(abs, ord)
    plt.xlabel("Mois")
    plt.ylabel("Nombre de projets en cours")
    plt.title("Projets en cours par mois")
    plt.tight_layout()
    plt.show()

    conn.close()