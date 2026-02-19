PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS statut_intervenant;
CREATE TABLE statut_intervenant (
    id_statut INTEGER PRIMARY KEY,
    statut    TEXT
);

DROP TABLE IF EXISTS client;
CREATE TABLE client (
    id_client INTEGER PRIMARY KEY,
    prenom    TEXT,
    nom       TEXT,
    secteur   TEXT,
    ville     TEXT,
    email     TEXT,
    telephone TEXT
);

DROP TABLE IF EXISTS intervenant;
CREATE TABLE intervenant (
    id_intervenant  INTEGER PRIMARY KEY,
    nom             TEXT,
    prenom          TEXT,
    telephone       TEXT,
    email           TEXT,
    annee_scolaire  TEXT,
    disponibilite   TEXT NOT NULL CHECK (disponibilite IN ('disponible','indisponible')),
    id_statut       INTEGER,
    FOREIGN KEY (id_statut) REFERENCES statut_intervenant(id_statut)
);

DROP TABLE IF EXISTS authentification;
CREATE TABLE authentification (
    id_intervenant INTEGER PRIMARY KEY,
    mot_de_passe   TEXT,
    FOREIGN KEY (id_intervenant) REFERENCES intervenant(id_intervenant)
);

DROP TABLE IF EXISTS projet;
CREATE TABLE projet (
    id_projet      INTEGER PRIMARY KEY,
    id_client      INTEGER,
    description    TEXT,
    statut         TEXT NOT NULL CHECK (statut IN ('en_cours','termine','en_negociation', 'en_attente_de_paiement')),
    date_creation  TEXT,
    date_fin       TEXT,
    remuneration   REAL,
    titre          TEXT,
    attentes       TEXT,
    budget         REAL,
    id_intervenant INTEGER,
    FOREIGN KEY (id_client) REFERENCES client(id_client),
    FOREIGN KEY (id_intervenant) REFERENCES intervenant(id_intervenant)
);

DROP TABLE IF EXISTS mission;
CREATE TABLE mission (
    id_mission     INTEGER PRIMARY KEY,
    id_projet      INTEGER,
    id_intervenant INTEGER,
    description    TEXT,
    date_debut     TEXT,
    date_fin       TEXT,
    statut         TEXT NOT NULL CHECK (statut IN ('en_cours','termine','en_negociation', 'en_attente_de_paiement')),
    FOREIGN KEY (id_projet) REFERENCES projet(id_projet),
    FOREIGN KEY (id_intervenant) REFERENCES intervenant(id_intervenant)
);

DROP TABLE IF EXISTS interaction;
CREATE TABLE interaction (
    id_interaction        INTEGER PRIMARY KEY,
    date                  TEXT,
    id_projet             INTEGER,
    id_client             INTEGER,
    id_intervenant        INTEGER,
    resume                TEXT,
    prochaine_interaction TEXT,
    type_interaction      TEXT,
    FOREIGN KEY (id_projet) REFERENCES projet(id_projet),
    FOREIGN KEY (id_client) REFERENCES client(id_client),
    FOREIGN KEY (id_intervenant) REFERENCES intervenant(id_intervenant)
);

DROP TABLE IF EXISTS competences;
CREATE TABLE competences (
    id_competence INTEGER PRIMARY KEY,
    competence    TEXT
);

DROP TABLE IF EXISTS competence_intervenant;
CREATE TABLE competence_intervenant (
    id_intervenant   INTEGER,
    id_competence    INTEGER,
    score_competence REAL,
    PRIMARY KEY (id_intervenant, id_competence),
    FOREIGN KEY (id_intervenant) REFERENCES intervenant(id_intervenant),
    FOREIGN KEY (id_competence) REFERENCES competences(id_competence)
);

DROP TABLE IF EXISTS competence_requise;
CREATE TABLE competence_requise (
    id_mission       INTEGER,
    id_competence    INTEGER,
    score_competence REAL,
    PRIMARY KEY (id_mission, id_competence),
    FOREIGN KEY (id_mission) REFERENCES mission(id_mission),
    FOREIGN KEY (id_competence) REFERENCES competences(id_competence)
);

DROP TABLE IF EXISTS document_intervenant;
CREATE TABLE document_intervenant (
    id_intervenant INTEGER,
    document       TEXT,
    FOREIGN KEY (id_intervenant) REFERENCES intervenant(id_intervenant)
);