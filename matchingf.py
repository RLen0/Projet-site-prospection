
#calcule la distance entre une mission et les intervenants, les trient, puis donne les candidats les plus aptes

import sqlite3
import math

def matching(id_mission_entree):
    
    BD= sqlite3.connect("DB/dataset3.db")
    BD.row_factory = sqlite3.Row
    curseur= BD.cursor()
   
    curseur.execute("SELECT id_competence FROM competences")
    L_competence = [row['id_competence'] for row in curseur.fetchall()]
    L_mission= []
    
    for b in enumerate(L_competence):
        curseur.execute( "SELECT score_competence FROM competence_requise WHERE id_competence = ? AND id_mission = ?", 
        (float(b[1]), id_mission_entree) )  
        
        bip = curseur.fetchone() 
        print(bip)
        if bip is not None and bip[0] is not None:
            L_mission.append(float(bip[0]))
        else:
            L_mission.append(0.0)

    
    curseur.execute("SELECT id_intervenant FROM intervenant WHERE disponibilite = 'disponible'")
    
    L_intervenant = [row['id_intervenant'] for row in curseur.fetchall()]
    L= []
    for b in enumerate(L_intervenant):
        L_inter=[]
        for c in enumerate(L_competence):
            curseur.execute("SELECT score_competence FROM competence_intervenant WHERE id_competence= ? AND id_intervenant = ?" , (c[1],b[1] ))
            comp = curseur.fetchall()
            if len(comp) > 0:
                L_inter.append(float(comp[0][0]))
            else:
                L_inter.append(0)
            
        L.append( [b[1], L_inter])

    print("L")
    print(L)

    
    L_final= []
    
    for k in range(len(L)):
        somme_carres = 0
        
        for i in range(len(L_competence)):
            somme_carres += (L[k][1][i] - L_mission[i])**2
        L_final.append([L[k][0], math.sqrt(somme_carres)])
    L_match = sorted(L_final, key=lambda x: x[1], reverse=False)

    BD.close()

    return [x[0] for x in L_match]

if __name__ == "__main__":
    print(matching(5))