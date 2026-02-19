import hashlib
import os
import pathlib
import sqlite3
import matchingf as match

from werkzeug.utils import secure_filename
import pandas as pd

from flask import Flask, render_template, request, redirect, session, url_for, abort, flash
from markupsafe import escape

app = Flask(__name__)
app.secret_key = "327c49af0e506bcca63fc0322a651cb7df0c7da77ff4f1749873362530c20488"
app.config['UPLOADED_FILES'] = 'static/files'
app.config['CACHE'] = 'static/cache'

@app.context_processor
def utility_processor():
    def into(e, l):
        return e in l
    return dict(into=into)

def hash_password(password):
    # Encode the password as bytes
    password_bytes = password.encode('utf-8')
    # Use SHA-256 hash function to create a hash object
    hash_object = hashlib.sha256(password_bytes)
    # Get the hexadecimal representation of the hash
    password_hash = hash_object.hexdigest()
    return password_hash

login_credentials = {"a.a@a.a":hash_password(""), # TODO : virer l'identifiant débug à la fin du projet
                     "rudy.lenoble@tnservice.net": "0b8e9e995d8d77f1e4770f0f79665aee6f3f70247b3735422daba73df4c3096f",
                     "oscar.millot@tnservices.net":"a153a673fd597fdedeeb88e6d6f1e0ae69d62d35a44a0c675a41ff1850e07651"}

def is_connected():
    return session.get("name", None) is not None

def verify_logged():
    if not is_connected():
         abort(401)
    return ()

def render(template, **kwargs):
    data_for_search = []
    if is_connected():
        conn=connection_a_la_bd()
        cur=conn.cursor()
        data_for_search.append(cur.execute("""SELECT DISTINCT projet.titre, client.nom as nom_client, projet.id_Projet FROM projet join client on client.id_Client == projet.id_Client""").fetchall())
        data_for_search.append(cur.execute("""SELECT DISTINCT client.nom, client.id_Client FROM client""").fetchall())
        data_for_search.append(cur.execute("""SELECT DISTINCT intervenant.nom, intervenant.id_intervenant from intervenant""").fetchall())
        conn.close()
    return render_template(template+'.html', user=session, data_for_search=data_for_search, **kwargs)

def connection_a_la_bd(need_log=True):
    if need_log:
        verify_logged() # commenter pour accéder à toutes les pages sans être déconnecter
    conn=sqlite3.connect("DB/dataset3.db")
    conn.row_factory=sqlite3.Row
    return conn

def call_DB_for(query, need_log=True):
    conn=connection_a_la_bd(need_log=need_log)
    cur=conn.cursor()
    cur.execute(query)
    result=cur.fetchall()
    conn.close()
    return result

@app.route('/')
def default():
    return redirect(url_for("login"))

@app.route('/login/', methods=['POST', 'GET'])
def login():
    if is_connected():
        return redirect("/tdb")
    elif request.method == 'POST':
        username = request.form['username']
        password = hash_password(request.form['password'])
        conn=connection_a_la_bd(need_log=False)
        cur=conn.cursor()
        cur.execute("""SELECT mot_de_passe FROM authentification
                             JOIN intervenant on authentification.id_intervenant = intervenant.id_intervenant
                             where intervenant.email = ?""",(username,))
        membre=cur.fetchall()
        conn.close()
        if membre:
            if membre[0]["mot_de_passe"] == password:
                u = username.split("@")[0].split(".")
                session["name"] = u[0].capitalize() + " " + u[1].upper()
                # print(escape(session["name"]))
                session["picture_filename"] = u[1].upper() + "_" + u[0].capitalize()
                # print(escape(session["picture_filename"]))
                return redirect("/tdb")
            else:
                return render("statics/login", user_name_placeholder=username, message="invalid")
        else:
            flash("Utilisateur inconnu", "error")
            return render("statics/login", user_name_placeholder=username, focus_password=username != "")

    else:
        username = escape(request.args.get('username', ''))
        message = escape(request.args.get('message', ''))
        return render("statics/login", user_name_placeholder=username, focus_password=username != "", message=message)


@app.route('/tdb/')
def tdb():
    conn=connection_a_la_bd()
    cur=conn.cursor()
    en_negociation=cur.execute(""" SELECT projet.titre,
                        projet.id_Projet,
                        client.nom AS client_nom,
                        projet.id_Client
            FROM main.projet
            JOIN client ON client.id_Client=projet.id_Client 
            WHERE projet.statut= 'en_negociation' """).fetchall()
    en_cours=cur.execute(""" SELECT projet.titre,
                        projet.id_Projet,
                        client.nom AS client_nom,
                        projet.id_Client
            FROM main.projet
            JOIN client ON client.id_Client=projet.id_Client 
            WHERE projet.statut= 'en_cours' """).fetchall()
    en_attente_de_paiement=cur.execute(""" SELECT projet.titre,
                        projet.id_Projet,
                        client.nom AS client_nom,
                        projet.id_Client
            FROM main.projet
            JOIN client ON client.id_Client=projet.id_Client 
            WHERE projet.statut= 'en_attente_de_paiement' """).fetchall()
    conn.close()
    data=[{"title": "En négociation ", "projets":en_negociation},{"title": "En cours ", "projets":en_cours},{"title": "En attente de paiement ", "projets":en_attente_de_paiement}]
    return render("standards/tdb", data=data)


@app.route('/projets/')
def list_projets(message=""):
    field_example = ["Titre", "Client", "Création", "Finalisation", "Modifications", "Status", "Documents"]
    field_db = "projet.titre, client.nom AS client_nom, projet.date_creation, projet.date_fin, projet.statut, projet.id_Projet, projet.id_Client"
    projets = call_DB_for(f"""SELECT {field_db}
                            FROM projet
                            LEFT JOIN client ON client.id_Client = projet.id_Client
                            ORDER BY projet.date_creation
                          """)
    return render("lists/list_projets", fields=field_example, projets=projets, message=message)

@app.route('/projet/<int:id>/', methods=['GET', 'POST'])
def projet(id):
    if id is not None:
        conn=connection_a_la_bd()
        cur=conn.cursor()
        cur.execute("""SELECT *, intervenant.nom as cdp FROM projet
                       JOIN intervenant on intervenant.id_intervenant = projet.id_intervenant
                       WHERE projet.id_projet = ? """, (id,))
        data_projet=cur.fetchone()
        if data_projet is not None:
            cur.execute("""SELECT DISTINCT mission.id_mission, mission.description, mission.statut, intervenant.nom, mission.date_debut, mission.date_fin
                           FROM projet 
                           JOIN mission on mission.id_Projet = projet.id_Projet
                           JOIN main.intervenant on mission.id_intervenant = intervenant.id_intervenant
                           WHERE projet.id_projet = ?  """, (id,))
            missions_projet=cur.fetchall()
            print("'''''''''''''''''''''''''''''''''''")
            missions_projet_split = []
            for mis in missions_projet:
                id_mis = (mis['id_mission'])
                missions_projet_split.append({"id":id_mis,"data": {data: mis[data] for data in ["description", "statut", "nom", "date_debut", "date_fin"]}})
            print(missions_projet[0].keys())
            conn.close()
            docs_projet = []
            print(str(id))
            pathlib.Path(os.path.join(f"{app.config['UPLOADED_FILES']}/documents", "projet", str(id))).mkdir(exist_ok=True)
            paths = list(pathlib.Path(os.path.join(f"{app.config['UPLOADED_FILES']}/documents", "projet", str(id))).walk())
            for path in paths:
                for filename in path[2]:
                    p = '/'.join(str(path[0]).split('/')[1:] + [filename])
                    print(p, '------------------------------')
                    docs_projet.append((p, filename))
            return render("standards/projet", projet=data_projet, missions_projet=missions_projet_split, docs_projet=docs_projet)
        else:
            conn.close()
            flash("Projet introuvable", "error")
    else:
        flash("Pas de projet donnée", "error")
    return redirect(url_for('list_projets'))

@app.post('/update_projet/<int:id>')
def update_projet(id):
    if request.method == 'POST':
        titre = request.form.get('titre')
        description = request.form.get('description')
        attentes = request.form.get('attentes')
        cdp = request.form.get('cdp')
        statut = request.form.get('statut')
        remuneration = request.form.get('remuneration')
        budget = request.form.get('budget')
        date_creation = request.form.get('date_creation')
        date_fin = request.form.get('date_fin')

        conn = connection_a_la_bd()
        cur = conn.cursor()
        id_intervenant = cur.execute("""SELECT id_intervenant FROM intervenant where nom = ?""", (cdp,)).fetchone()[0]
        conn.close()



        update_statement = 'UPDATE projet SET titre=?, description=?, attentes=?, statut=?, remuneration=?, budget=?, date_creation=?, date_fin=?, id_intervenant=? WHERE id_Projet = ?'
        conn = connection_a_la_bd()
        cur = conn.cursor()
        cur.execute(update_statement, (titre, description, attentes, statut, remuneration, budget, date_creation, date_fin, id_intervenant, id,))
        conn.commit()
        conn.close()
        flash("Changements effectués", "success")
    return redirect(url_for('projet', id=id))

@app.route('/mission/<int:id>/', methods=['GET', 'POST'])
def mission(id):
    if id is not None:
        conn=connection_a_la_bd()
        cur=conn.cursor()
        cur.execute("""SELECT *, intervenant.nom FROM mission
                    JOIN intervenant on intervenant.id_intervenant = mission.id_intervenant
                    WHERE mission.id_mission == ?""", (id,))
        data_mission=cur.fetchone()
        if data_mission is not None:
            cur.execute("""SELECT * FROM competences""")
            list_competences=cur.fetchall()
            cur.execute("""SELECT * FROM competences
                        JOIN competence_requise on competences.id_competence = competence_requise.id_competence
                        WHERE id_mission = ?""", (id,))
            competences_mission=cur.fetchall()
            docs_mission = []
            pathlib.Path(os.path.join(f"{app.config['UPLOADED_FILES']}/documents", "mission", str(id))).mkdir(exist_ok=True)
            paths = list(pathlib.Path(os.path.join(f"{app.config['UPLOADED_FILES']}/documents", "mission", str(id))).walk())
            for path in paths:
                for filename in path[2]:
                    p = '/'.join(str(path[0]).split('/')[1:] + [filename])
                    print(p, '------------------------------')
                    docs_mission.append((p, filename))
            matching_ids = match.matching(id)
            matching_list = []
            for id_int in matching_ids:
                cur.execute("SELECT intervenant.nom FROM intervenant WHERE id_intervenant = ?", (id_int,))
                result=cur.fetchall()
                matching_list.append({"id": id_int, "name": result[0][0]})
            conn.close()
            print(matching_list)
            return render("standards/mission", mission=data_mission, list_competences=list_competences, competences_mission=competences_mission, docs_mission=docs_mission, matching=matching_list)
        else:
            conn.close()
            flash("Mission introuvable", "error")
    else:
        flash("Pas de mission donnée", "error")
    return redirect(url_for('list_projets'))

@app.post('/update_mission/<int:id>')
def update_mission(id):
    if request.method == 'POST':
        description = request.form.get('description')
        statut = request.form.get('statut')
        intervenant = request.form.get('intervenant')
        competence = request.form.get('competence')
        date_debut = request.form.get('date_debut')
        date_fin = request.form.get('date_fin')
        print(competence)

        # conn = connection_a_la_bd()
        # cur = conn.cursor()
        # id_intervenant = cur.execute("""SELECT id_intervenant FROM intervenant where nom = ?""", (cdp,)).fetchone()[0]
        # conn.close()

        update_statement = 'UPDATE mission SET description=?, statut=?, date_debut=?, date_fin=?, id_intervenant=? WHERE id_mission = ?'
        conn = connection_a_la_bd()
        cur = conn.cursor()
        cur.execute(update_statement, (description, statut, date_debut, date_fin, intervenant, id,))
        conn.commit()
        conn.close()
        flash("Changements effectués", "success")
    return redirect(url_for('mission', id=id))

@app.route('/new_projet/', methods=["GET","POST"])
def new_projet():
    if request.method== "POST" :
        statut='en_cours'
        nom_projet=request.form.get("titre")#recuperation des données 
        client=request.form.get("client")
        chefprojet=request.form.get("chefprojet")
        date=request.form.get("Date")
        remunération=request.form.get('rémunération')
        competence=request.form.get('competences')
        intervenant=request.form.get('intervenant')
        description=request.form.get('description')
        date_fin=request.form.get('datef')
        print(nom_projet, client , chefprojet , competence , intervenant , description )#sert à vérifier dans le terminal que les donées arrivent bien depuis le formulaire 
        conn=connection_a_la_bd()
        cur=conn.cursor()
        cur.execute( "SELECT id_client FROM client WHERE nom = ?",(client,))#recherche un client avec ce nom pour voir s'il existe déjà
        row = cur.fetchone()
        if row: #si il existe on récupère son id 
            id_client = row[0]       
        else:#sinon on l'insère comme nouveau client 
             cur.execute("INSERT INTO client (nom) VALUES (?)",(client,))
             id_client = cur.lastrowid #genere un nouvel identifiant qu'on récupère
        cur.execute( "SELECT id_intervenant FROM INTERVENANT WHERE nom = ?",(chefprojet,)) #meme logique pour intervenant 
        row = cur.fetchone()
        statut='en_cours'
        if row:
            id_chef_de_projet = row[0]       
        else:
             disponibilité='disponible'
             cur.execute("INSERT INTO INTERVENANT (nom,disponibilite) VALUES (?,?)",(chefprojet,disponibilité))
             id_chef_de_projet = cur.lastrowid
        cur.execute("""INSERT INTO PROJET ( titre , id_client , id_intervenant ,description , statut , date_creation,date_fin)
                        VALUES ( ?,?,?,?,?,?,?) """ , (nom_projet, id_client , id_chef_de_projet ,description, statut,date,date_fin))  #on crée un nouveau projet 
        id_projet= cur.lastrowid # on récupère l'id du projet 
        print("ID projet crée : " , id_projet)
        print("colonnes insérées:", cur.rowcount)
        cur.execute("""INSERT INTO mission ( id_projet, id_intervenant,statut) VALUES (?, ?,?)""", (id_projet, chefprojet ,statut)) #on insere id_projet et id_chef_de_projet 
        conn.commit()
        conn.close()
        return redirect(url_for("projet", id=id_projet))
    return render('new/new_projet')




@app.route('/clients/')
def list_clients():
    conn=connection_a_la_bd()
    cur=conn.cursor()
    cur.execute("""
        SELECT
            client.nom,
            client.id_Client,
            COUNT(projet.id_projet) AS nb_proposes,
            SUM(CASE WHEN projet.statut = 'en_cours' THEN 1 ELSE 0 END) AS nb_en_cours
        FROM client
        LEFT JOIN projet ON projet.id_Client = client.id_Client
        GROUP BY client.id_Client""")
    c=cur.fetchall()
    conn.close()
    return render("lists/list_clients", clients=c)



@app.route('/client/<int:id>/', methods=['GET', 'POST'])
def client(id):
    if id is not None:
        conn=connection_a_la_bd()
        cur=conn.cursor()
        cur.execute("SELECT * FROM client WHERE id_Client = ? ", (id,))
        data_client=cur.fetchone()
        if data_client is not None:
            cur.execute("SELECT titre, statut, date_creation, date_fin FROM projet WHERE projet.id_Client = ?  ",(id,))
            projets_client=cur.fetchall()
            conn.close()
            docs_client = []
            pathlib.Path(os.path.join(f"{app.config['UPLOADED_FILES']}/documents", "client", str(id))).mkdir(exist_ok=True)
            paths = list(pathlib.Path(os.path.join(f"{app.config['UPLOADED_FILES']}/documents", "client", str(id))).walk())
            for path in paths:
                for filename in path[2]:
                    p = '/'.join(str(path[0]).split('/')[1:] + [filename])
                    print(p, '------------------------------')
                    docs_client.append((p, filename))
            return render("standards/client", client=data_client, projets_client=projets_client, docs_client=docs_client)
        else:
            conn.close()
            flash("Client introuvable", "error")
    else:
        flash("Pas de client donnée", "error")
    return redirect(url_for('list_clients'))

@app.post('/update_client/<int:id>')
def update_client(id):
    if request.method == 'POST':
        nom = request.form.get('nom')
        secteur = request.form.get('secteur')
        ville = request.form.get('ville')
        update_statement = 'UPDATE client SET nom=?, secteur=?, ville=? WHERE id_Client = ?'
        conn = connection_a_la_bd()
        cur = conn.cursor()
        cur.execute(update_statement, (nom, secteur, ville, id,))
        conn.commit()
        conn.close()
        flash("Changements effectués", "success")
    return redirect(url_for('client', id=id))

@app.post('/delete_client/<int:id>')
def delete_client(id):
    # if request.method == 'POST':
    #     nom = request.form.get('nom')
    #     secteur = request.form.get('secteur')
    #     ville = request.form.get('ville')
    #     update_statement = 'UPDATE client SET nom=?, secteur=?, ville=? WHERE id_Client = ?'
    #     conn = connection_a_la_bd()
    #     cur = conn.cursor()
    #     cur.execute(update_statement, (nom, secteur, ville, id,))
    #     conn.commit()
    #     conn.close()
    # TODO
    return redirect(url_for('list_client'))

@app.route('/new_client/', methods=["GET","POST"])
def new_client():
    if request.method=='POST':
        nom=request.form.get('nom')
        telephone=request.form.get('telephone')
        ville=request.form.get('ville')
        email=request.form.get('email')
        secteur=request.form.get('secteur')
        intervenant=request.form.get('intervenant')
        conn=connection_a_la_bd()
        cur=conn.cursor()
        cur.execute('INSERT INTO client (nom , telephone, ville , email,secteur) VALUES (?,?,?,?,?)',((nom , telephone, ville , email, secteur)))
        conn.commit()
        id_client=cur.execute('SELECT id_client FROM client WHERE nom=? AND telephone=?',(nom,telephone)).fetchone()[0]
        conn.close()
        return redirect(url_for('client', id=id_client))
    return render('new/new_client')




@app.route('/intervenants/')
def list_intervenants(message=""):
    conn=connection_a_la_bd()
    cur=conn.cursor()
    cur.execute(""" SELECT 
            intervenant.id_intervenant,
           intervenant.nom,
        COUNT(mission.id_mission) AS nb_missions,
        SUM ( CASE WHEN mission.statut='en_cours' THEN 1 ELSE 0 END ) AS nb_en_cours
    FROM intervenant
    LEFT JOIN mission ON mission.id_intervenant=intervenant.id_intervenant 
    LEFT JOIN projet ON intervenant.id_intervenant = projet.id_intervenant
    GROUP BY  intervenant.id_intervenant, intervenant.nom""")
    i=cur.fetchall()
    conn.close()
    return render("lists/list_intervenants", intervenants=i, message=message)

@app.route('/intervenant/<int:id>/', methods=['GET', 'POST'])
def intervenant(id):
    if id is not None:
        conn=connection_a_la_bd()
        cur=conn.cursor()
        cur.execute("""SELECT *, statut FROM intervenant
                       JOIN statut_intervenant on statut_intervenant.id_statut == intervenant.id_statut
                       WHERE id_intervenant = ? """, (id,))
        data_intervenant=cur.fetchone()
        if data_intervenant is not None:
            cur.execute("""SELECT DISTINCT titre, projet.statut, date_creation, projet.date_fin FROM projet 
                           JOIN main.mission on mission.id_Projet = projet.id_Projet
                           WHERE mission.id_intervenant = ?  """, (id,))
            projets_intervenant=cur.fetchall()
            conn.close()
            docs_intervenant = []
            pathlib.Path(os.path.join(f"{app.config['UPLOADED_FILES']}/documents", "intervenant", str(id))).mkdir(exist_ok=True)
            paths = list(pathlib.Path(os.path.join(f"{app.config['UPLOADED_FILES']}/documents", "intervenant", str(id))).walk())
            for path in paths:
                for filename in path[2]:
                    p = '/'.join(str(path[0]).split('/')[1:] + [filename])
                    print(p, '------------------------------')
                    docs_intervenant.append((p, filename))
            return render("standards/intervenant", intervenant=data_intervenant, projets_intervenant=projets_intervenant, docs_intervenant=docs_intervenant)
        else:
            conn.close()
            flash("Intervenant introuvable", "error")
    else:
        flash("Pas d'intervenant donnée", "error")
    return redirect(url_for('list_intervenants'))

@app.post('/update_intervenant/<int:id>')
def update_intervenant(id):
    if request.method == 'POST':
        nom = request.form.get('nom')
        telephone = request.form.get('telephone')
        email = request.form.get('email')
        annee_scolaire = request.form.get('annee_scolaire')
        disponibilite = request.form.get('disponibilite')
        statut = request.form.get('statut')
        conn = connection_a_la_bd()
        cur = conn.cursor()
        id_statut_cur = cur.execute("""SELECT id_statut FROM statut_intervenant where statut = ?""", (statut,))
        id_statut = id_statut_cur.fetchone()[0]
        conn.close()

        update_statement = 'UPDATE intervenant SET nom=?, telephone=?, email=?, annee_scolaire=?, disponibilite=?, id_statut=? WHERE id_intervenant = ?'
        conn = connection_a_la_bd()
        cur = conn.cursor()
        cur.execute(update_statement, (nom, telephone, email, annee_scolaire, disponibilite, id_statut, id,))
        conn.commit()
        conn.close()
        flash("Changements effectués", "success")
    return redirect(url_for('intervenant', id=id))

@app.route('/new_intervenant/', methods=["GET","POST"])
def new_intervenant():
    if request.method=='POST':
        nom=request.form.get('nom')
        prenom=request.form.get('prenom')
        annee_scolaire=request.form.get('annee_scolaire')
        email=request.form.get('email')
        disponibilite=request.form.get('disponibilite')
        competence=request.form.get('competence')
        conn=connection_a_la_bd()
        cur=conn.cursor()
        cur.execute('SELECT id_intervenant FROM intervenant WHERE nom=? AND prenom=?',(nom,prenom))
        row=cur.fetchone()
        if row : 
            id_intervenant=row['id_intervenant']
        else : 
            cur.execute('INSERT INTO intervenant (nom , prenom , annee_scolaire , email , disponibilite ) VALUES (?,?,?,?,?)',(nom , prenom , annee_scolaire , email , disponibilite ) )
            conn.commit()
            id_intervenant=cur.lastrowid
        cur.execute('SELECT id_competence FROM competences WHERE competence=?',(competence,))
        row=cur.fetchone()
        if row : 
            id_competence=row['id_competence']
        else :
            cur.execute ('INSERT INTO competences (competence) VALUES(?)',(competence,)) 
            id_competence=cur.lastrowid    
        cur.execute('INSERT INTO competence_intervenant(id_intervenant,id_competence) VALUES (?,?)',(id_intervenant,id_competence))
        conn.commit()
        conn.close()
        return redirect(url_for("intervenant", id=id_intervenant))
    return render('new/new_intervenant')



@app.route('/membres/')
def list_membres(message=""):
    conn=connection_a_la_bd()
    cur=conn.cursor()
    cur.execute(""" SELECT intervenant.nom,
     intervenant.id_intervenant as id_Membre,
     statut_intervenant.statut, 
     intervenant.annee_scolaire 
     FROM intervenant 
     LEFT JOIN statut_intervenant ON statut_intervenant.id_statut=intervenant.id_statut 
     WHERE statut_intervenant.statut!='Externe'
     """)
    membres=cur.fetchall()
    conn.close() 
    return render("lists/list_membres", membres=membres, message=message)

@app.route('/membre/<int:id>/')
def membre(id=None):
    conn=connection_a_la_bd()
    cur=conn.cursor()
    if id is None: # TODO : ajoute ou si on ne trouve pas le projet associé dans la DB
        redirect(url_for('list_membres', message="not found"))
    cur.execute(""" SELECT intervenant.nom ,
    intervenant.prénom , 
    statut_intervenant.statut , 
    intervenant.année_scolaire 
    FROM intervenant 
    LEFT JOIN statut_intervenant ON statut_intervenant.id_statut=intervenant.id_statut 
    WHERE statut_intervenant.statut!='Externe'
    """,(id,))
    membre=cur.fetchone()
    conn.close()
    return render("standards/membre", membre=membre)

@app.post('/update_membre/<int:id>')
def update_membre(id):
    if request.method == 'POST':
        nom = request.form.get('nom')
        secteur = request.form.get('secteur')
        ville = request.form.get('ville')
        update_statement = 'UPDATE client SET nom=?, secteur=?, ville=? WHERE id_Client = ?'
        conn = connection_a_la_bd()
        cur = conn.cursor()
        cur.execute(update_statement, (nom, secteur, ville, id,))
        conn.commit()
        conn.close()
    return redirect(url_for('client', id=id))

@app.route('/new_membre/', methods=['POST','GET'])
def new_membre():
    if request.method=='POST':
        nom=request.form.get("nom")
        prenom=request.form.get("prenom")
        annee=request.form.get("annee")
        statut=request.form.get("statut")
        conn=connection_a_la_bd()
        cur=conn.cursor()
        cur.execute("""SELECT id_statut FROM statut_intervenant WHERE statut = ?""", (statut,))
        statut = cur.fetchone()
        if statut is None:
            conn.close()
            flash("Statut invalide ou inexistant , vérifiez l'orthographe", "error")
            return render( "new/new_membre")
        id_statut = statut["id_statut"]
        disponibilite='disponible'
        cur.execute("""INSERT INTO intervenant (nom, prenom, annee_scolaire,disponibilite, id_statut) VALUES (?, ?, ?, ?,?)""", (nom, prenom, annee,disponibilite, id_statut))
        conn.commit()
        # conn.close()
        # conn=connection_a_la_bd()
        # cur=conn.cursor()
        id_intervenant=cur.execute('SELECT id_intervenant FROM intervenant WHERE nom=? AND prenom= ? ',(nom,prenom,)).fetchone()[0]
        conn.close()
        return redirect(url_for("intervenant", id=id_intervenant))
    return render('new/new_membre')



@app.route('/cdp/')
def list_cdp():
    return render("lists/list_cdp")

# from statistiques.Nbr_client import nbr_client
# from statistiques.Projets_en_cours import projet_en_cours
# from statistiques.repartition_projets_ import secteur

@app.route('/stats/')
def stats():
    return ""
    # # Les données à entrer en arguments des fonctions sont à définir une fois que j'aurai les ofnctions.
    # graphe_client  = nbr_client(dataset, Date)
    # graphe_projet = projet_en_cours(...)
    # repartition_projet = secteur(...)
    # return render("gestions/stats", Nombre_client = graphe_client, Projet_en_cours = graphe_projet, Repart_projet = repartition_projet)

@app.route('/acces/')
def acces():
    return render("gestions/acces")

@app.route('/import_doc/<string:entite>/<int:id>', methods=['GET', 'POST'])
def import_doc(entite, id):
    entite = escape(entite)
    if escape(entite) not in ["projet", "client", "intervenant", "membre", "mission"]:
        abort(404)
    verify_logged()
    # TODO : temporaire - il faudra faire l'ajout automatique du dossier correspondant à la création de l'instance
    if request.method == 'POST':
        # check if the post request has the file part
        if 'files' not in request.files:
            flash('No file part', 'error')
        else:
            files = request.files.getlist('files')
            # If the user does not select a file, the browser submits an
            # empty file without a filename.
            print(files, "---------------------------------------")
            for file in files:
                if file.filename == "":
                    flash('No selected file', 'error')
                else:
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(f"{app.config['UPLOADED_FILES']}/documents", entite, str(id), filename))
        return redirect(url_for(entite, id=id))

@app.route('/delete_doc/', methods = ['POST', 'GET'])
def delete_doc():
    print("--------------------------------------===================")
    print(request.from_values())
    verify_logged()
    path = request.form.get("path", None)
    from_page = request.form.get("from", 'default')
    if path is not None:
        path = url_for('static', filename=path)
        print("path =", path)
        os.remove('.'+path)
    else:
        flash("Fichier introuvable", "error")

    return redirect(from_page)

@app.route('/import_csv/<string:entite>', methods=['POST'])
def import_csv(entite):
    entite = escape(entite)
    if escape(entite) not in ["projets", "clients", "intervenants", "membres"]:
        abort(404)
    if 'file' not in request.files:
        flash('No file part', 'error')
    else:
        file = request.files.get('file')
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        filename = secure_filename(file.filename)
        if filename == "":
            flash('No selected file', 'error')
        else:
            file.save(os.path.join(app.config['CACHE'], filename))
            cached_file_path = os.path.join(app.config['CACHE'], filename)
            print(cached_file_path)
            conn=connection_a_la_bd()
            print("add =", pd.read_csv(cached_file_path).to_sql(entite[:-1], conn, if_exists='append', index=False))
            os.remove(cached_file_path)
    return redirect(url_for('list_'+entite))

@app.route('/export/<string:entite>/')
def export_csv(entite):
    entite = escape(entite)
    if escape(entite) not in ["projets", "clients", "intervenants", "membres"]:
        abort(404)
    query = f"SELECT * FROM {entite[:-1]}"
    conn = connection_a_la_bd()
    data_frame = pd.read_sql(query, conn)
    conn.close()
    return data_frame.to_csv(index=False)

@app.route('/delete/<string:entite>/<int:id>/', methods=['GET', 'POST'])
def delete(entite, id):
    delete_statement = f"DELETE FROM {entite} WHERE id_{entite} = ?"
    conn = connection_a_la_bd()
    conn.cursor().execute(delete_statement, (id,))
    conn.commit()
    conn.close()
    return redirect(url_for(f"list_{entite}s"))


@app.route('/logout/')
def logout():
    session.pop("name", None)
    session.pop("picture_filemane", None)
    return redirect(url_for('login', message='success'))

@app.route('/rgpd/')
def rgpd():
    return render("statics/rgpd")

@app.errorhandler(401)
def denied(error):
    return redirect(url_for('login', message='denied'))

@app.errorhandler(404)
def page_not_found(error):
    return render("statics/page_not_found", error=error, title="Error"), 404



# Dossiers nécéssaires
pathlib.Path("static", "files").mkdir(exist_ok=True)
pathlib.Path("static", "cache").mkdir(exist_ok=True)
pathlib.Path(f"{app.config['UPLOADED_FILES']}", "documents").mkdir(exist_ok=True)
pathlib.Path(f"{app.config['UPLOADED_FILES']}/documents/", "client").mkdir(exist_ok=True)
pathlib.Path(f"{app.config['UPLOADED_FILES']}/documents/", "projet").mkdir(exist_ok=True)
pathlib.Path(f"{app.config['UPLOADED_FILES']}/documents/", "intervenant").mkdir(exist_ok=True)
pathlib.Path(f"{app.config['UPLOADED_FILES']}/documents/", "membre").mkdir(exist_ok=True)
pathlib.Path(f"{app.config['UPLOADED_FILES']}/documents/", "mission").mkdir(exist_ok=True)

app.run(debug=True)
