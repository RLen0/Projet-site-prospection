PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS client;
CREATE TABLE client (
    id_Client TEXT PRIMARY KEY,
    prenom    TEXT,
    nom       TEXT,
    secteur   TEXT,
    ville     TEXT
);

DROP TABLE IF EXISTS intervenant;
CREATE TABLE intervenant (
    id_intervenant  TEXT PRIMARY KEY,
    nom             TEXT,
    prénom          TEXT,
    téléphone       TEXT,
    email           TEXT,
    année_scolaire  TEXT,
    disponibilité   TEXT NOT NULL CHECK (disponibilité IN ('disponible','indisponible')) 
    id_statut       TEXT
);

DROP TABLE IF EXISTS authentification;
CREATE TABLE authentification (
    id_intervenant TEXT PRIMARY KEY,
    mot_de_passe   TEXT,
    FOREIGN KEY (id_intervenant) REFERENCES intervenant(id_intervenant)
);

DROP TABLE IF EXISTS projet;
CREATE TABLE projet (
    id_Projet      TEXT PRIMARY KEY,
    id_Client      TEXT,
    description    TEXT,
    statut         TEXT NOT NULL CHECK (statut IN ('en_cours','à faire','terminé')),
    date_créatiion TEXT,
    date_fin       TEXT,
    rémunération   REAL,
    titre          TEXT,
    budget         REAL,
    id_chef_de_projet INTEGER 
FOREIGN KEY  (id_chef_de_projet) REFERENCES intervenant(id_intervenant) 
);

DROP TABLE IF EXISTS mission;
CREATE TABLE mission (
    id_mission     TEXT PRIMARY KEY,
    id_Projet      TEXT,
    id_intervenant TEXT,
    description    TEXT,
    date_debut     TEXT,
    date_fin       TEXT,
    statut         TEXT
);

DROP TABLE IF EXISTS interaction;
CREATE TABLE interaction (
    id_interaction        TEXT PRIMARY KEY,
    date                  TEXT,
    projet                TEXT,
    id_Client             TEXT,
    id_intervenant        TEXT,
    resumé                TEXT,
    prochaine_interaction TEXT,
    type_interaction      TEXT
);

DROP TABLE IF EXISTS competances;
CREATE TABLE competances (
    id_competance TEXT PRIMARY KEY,
    competance    TEXT
);

DROP TABLE IF EXISTS competance_intervenant;
CREATE TABLE competance_intervenant (
    id_intervenant   TEXT,
    id_competance    TEXT,
    score_competance REAL,
    PRIMARY KEY (id_intervenant, id_competance)
);

DROP TABLE IF EXISTS competance_requise;
CREATE TABLE competance_requise (
    id_mission       TEXT,
    id_competance    TEXT,
    score_competance REAL,
    PRIMARY KEY (id_mission, id_competance)
);

DROP TABLE IF EXISTS document_intervenant;
CREATE TABLE document_intervenant (
    id_intervenant TEXT,
    document       TEXT
);
CREATE TABLE statut_intervenant (
  id_statut TEXT PRIMARY KEY,
  statut    TEXT NOT NULL UNIQUE
);
