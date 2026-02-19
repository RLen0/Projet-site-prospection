import matplotlib.pyplot as plt 
import sqlite3


def secteur():
    BD= sqlite3.connect("dataset3.db")
    BD.row_factory = sqlite3.Row
    curseur= BD.cursor()
    res = curseur.execute("""SELECT c.secteur, COUNT(p.id_projet)
        FROM client c
        LEFT JOIN projet p ON c.id_client = p.id_client
        GROUP BY c.secteur""").fetchall()
    abs = [r[0] for r in res]
    ord = [r[1] for r in res]

    plt.bar(abs, ord)
    plt.xlabel("Secteur")
    plt.ylabel("Nombre de projets")
    plt.title("Répartition des projets par secteur")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.show()
    BD.close()

secteur()

