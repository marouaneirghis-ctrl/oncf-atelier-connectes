import sqlite3
from datetime import datetime, timedelta

# Initialisation de la base de données
def init_db():
    conn = sqlite3.connect('oncf.db')
    c = conn.cursor()
    
    # Création des tables
    c.execute('''CREATE TABLE IF NOT EXISTS utilisateurs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  nom TEXT NOT NULL,
                  email TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL,
                  role TEXT NOT NULL)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS trains
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  modele TEXT NOT NULL,
                  date_mise_en_service TEXT NOT NULL,
                  km_total INTEGER DEFAULT 0,
                  etat_sante REAL DEFAULT 100,
                  derniere_visite TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS anomalies
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  train_id INTEGER NOT NULL,
                  technicien_id INTEGER NOT NULL,
                  date_signalement TEXT NOT NULL,
                  categorie TEXT NOT NULL,
                  composant TEXT NOT NULL,
                  description TEXT NOT NULL,
                  criticite_calculée REAL NOT NULL,
                  urgence TEXT NOT NULL,
                  statut TEXT DEFAULT 'en_cours',
                  FOREIGN KEY(train_id) REFERENCES trains(id),
                  FOREIGN KEY(technicien_id) REFERENCES utilisateurs(id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS conformites
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  train_id INTEGER NOT NULL,
                  technicien_id INTEGER NOT NULL,
                  date_intervention TEXT NOT NULL,
                  type_intervention TEXT NOT NULL,
                  piece_remplacee TEXT,
                  resultat TEXT NOT NULL,
                  observations TEXT,
                  FOREIGN KEY(train_id) REFERENCES trains(id),
                  FOREIGN KEY(technicien_id) REFERENCES utilisateurs(id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS pieces
                 (reference TEXT PRIMARY KEY,
                  designation TEXT NOT NULL,
                  quantite_disponible INTEGER NOT NULL,
                  seuil_min INTEGER NOT NULL,
                  utilise_dans TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS criticite_components
                 (composant TEXT PRIMARY KEY,
                  criticite_max INTEGER NOT NULL)''')
    
    # Données initiales
    if not c.execute("SELECT * FROM utilisateurs").fetchone():
        c.execute("INSERT INTO utilisateurs (nom, email, password, role) VALUES (?, ?, ?, ?)",
                  ('Admin', 'admin@oncf.ma', 'admin123', 'responsable'))
        c.execute("INSERT INTO utilisateurs (nom, email, password, role) VALUES (?, ?, ?, ?)",
                  ('Tech1', 'tech1@oncf.ma', 'tech123', 'technicien'))
    
    if not c.execute("SELECT * FROM trains").fetchone():
        c.execute("INSERT INTO trains (modele, date_mise_en_service) VALUES (?, ?)",
                  ('Z2M-001', '2020-01-15'))
        c.execute("INSERT INTO trains (modele, date_mise_en_service) VALUES (?, ?)",
                  ('Z2M-002', '2020-03-22'))
    
    if not c.execute("SELECT * FROM criticite_components").fetchone():
        composants = [
            ('Moteur', 80),
            ('Freins', 90),
            ('Batterie', 70),
            ('Compresseur', 60),
            ('Suspension', 50),
            ('Climatisation', 40),
            ('Portes', 30),
            ('Eclairage', 20)
        ]
        c.executemany("INSERT INTO criticite_components VALUES (?, ?)", composants)
    
    if not c.execute("SELECT * FROM pieces").fetchone():
        pieces = [
            ('MOT-Z2M-001', 'Moteur Z2M', 5, 2, 'Moteur'),
            ('FRE-Z2M-001', 'Kit freins complet', 10, 4, 'Freins'),
            ('BAT-Z2M-001', 'Batterie 24V', 8, 3, 'Batterie'),
            ('CLIM-Z2M-001', 'Unité climatisation', 3, 1, 'Climatisation')
        ]
        c.executemany("INSERT INTO pieces VALUES (?, ?, ?, ?, ?)", pieces)
    
    conn.commit()
    conn.close()

# Fonctions d'accès aux données
def authentifier_utilisateur(email, password):
    conn = sqlite3.connect('oncf.db')
    c = conn.cursor()
    c.execute("SELECT * FROM utilisateurs WHERE email=? AND password=?", (email, password))
    user = c.fetchone()
    conn.close()
    
    if user:
        return {
            'id': user[0],
            'nom': user[1],
            'email': user[2],
            'role': user[3]
        }
    return None

def get_trains():
    conn = sqlite3.connect('oncf.db')
    c = conn.cursor()
    c.execute("SELECT * FROM trains")
    trains = [{
        'id': row[0],
        'modele': row[1],
        'date_mise_en_service': row[2],
        'km_total': row[3],
        'etat_sante': row[4],
        'derniere_visite': row[5]
    } for row in c.fetchall()]
    conn.close()
    return trains

def get_composants_par_categorie():
    # Cette fonction peut être adaptée selon votre structure réelle
    return {
        'mécanique': ['Moteur', 'Freins', 'Suspension'],
        'électrique': ['Batterie', 'Eclairage'],
        'climatisation': ['Climatisation'],
        'autre': ['Portes', 'Sièges']
    }

def get_criticite_composant(composant):
    conn = sqlite3.connect('oncf.db')
    c = conn.cursor()
    c.execute("SELECT criticite_max FROM criticite_components WHERE composant=?", (composant,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 50

def get_frequence_pannes(train_id, composant):
    conn = sqlite3.connect('oncf.db')
    c = conn.cursor()
    c.execute("""SELECT COUNT(*) FROM anomalies 
                 WHERE train_id=? AND composant=? AND date_signalement >= date('now', '-6 months')""",
              (train_id, composant))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0

def ajouter_anomalie(train_id, technicien_id, categorie, composant, description, criticite_calculée, urgence):
    conn = sqlite3.connect('oncf.db')
    c = conn.cursor()
    c.execute("""INSERT INTO anomalies 
                 (train_id, technicien_id, date_signalement, categorie, composant, description, criticite_calculée, urgence)
                 VALUES (?, ?, datetime('now'), ?, ?, ?, ?, ?)""",
              (train_id, technicien_id, categorie, composant, description, criticite_calculée, urgence))
    conn.commit()
    conn.close()

def mettre_a_jour_etat_train(train_id, etat_sante):
    conn = sqlite3.connect('oncf.db')
    c = conn.cursor()
    c.execute("UPDATE trains SET etat_sante=?, derniere_visite=datetime('now') WHERE id=?", 
              (etat_sante, train_id))
    conn.commit()
    conn.close()

def get_anomalies_technicien(technicien_id, statut='tous', urgence='tous', limit=None):
    conn = sqlite3.connect('oncf.db')
    c = conn.cursor()
    
    query = "SELECT * FROM anomalies WHERE technicien_id=?"
    params = [technicien_id]
    
    if statut != 'tous':
        query += " AND statut=?"
        params.append(statut)
    
    if urgence != 'tous':
        query += " AND urgence=?"
        params.append(urgence)
    
    query += " ORDER BY date_signalement DESC"
    
    if limit:
        query += " LIMIT ?"
        params.append(limit)
    
    c.execute(query, tuple(params))
    anomalies = [{
        'id': row[0],
        'train_id': row[1],
        'technicien_id': row[2],
        'date_signalement': row[3],
        'categorie': row[4],
        'composant': row[5],
        'description': row[6],
        'criticite_calculée': row[7],
        'urgence': row[8],
        'statut': row[9]
    } for row in c.fetchall()]
    
    conn.close()
    return anomalies

def get_anomalies(statut='tous', urgence='tous'):
    return get_anomalies_technicien(None, statut, urgence)

def get_anomalies_recentes(train_id, jours=90):
    conn = sqlite3.connect('oncf.db')
    c = conn.cursor()
    c.execute("""SELECT * FROM anomalies 
                 WHERE train_id=? AND date_signalement >= date('now', ?) 
                 ORDER BY date_signalement DESC""",
              (train_id, f'-{jours} days'))
    anomalies = [{
        'id': row[0],
        'train_id': row[1],
        'technicien_id': row[2],
        'date_signalement': row[3],
        'categorie': row[4],
        'composant': row[5],
        'description': row[6],
        'criticite_calculée': row[7],
        'urgence': row[8],
        'statut': row[9]
    } for row in c.fetchall()]
    conn.close()
    return anomalies

def ajouter_conformite(train_id, technicien_id, type_intervention, composant, piece_remplacee, resultat, observations):
    conn = sqlite3.connect('oncf.db')
    c = conn.cursor()
    c.execute("""INSERT INTO conformites 
                 (train_id, technicien_id, date_intervention, type_intervention, composant, piece_remplacee, resultat, observations)
                 VALUES (?, ?, datetime('now'), ?, ?, ?, ?, ?)""",
              (train_id, technicien_id, type_intervention, composant, piece_remplacee, resultat, observations))
    conn.commit()
    conn.close()

def marquer_anomalies_resolues(train_id, composant):
    conn = sqlite3.connect('oncf.db')
    c = conn.cursor()
    c.execute("""UPDATE anomalies SET statut='résolue' 
                 WHERE train_id=? AND composant=? AND statut='en_cours'""",
              (train_id, composant))
    conn.commit()
    conn.close()

def get_pieces():
    conn = sqlite3.connect('oncf.db')
    c = conn.cursor()
    c.execute("SELECT * FROM pieces")
    pieces = [{
        'reference': row[0],
        'designation': row[1],
        'quantite_disponible': row[2],
        'seuil_min': row[3],
        'utilise_dans': row[4]
    } for row in c.fetchall()]
    conn.close()
    return pieces

def get_historique_etats(jours=30):
    conn = sqlite3.connect('oncf.db')
    c = conn.cursor()
    
    # Pour chaque jour, récupérer l'état moyen des trains
    dates = []
    etats_moyens = []
    
    for i in range(jours, -1, -1):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        c.execute("""SELECT AVG(etat_sante) FROM trains""")
        etat_moyen = c.fetchone()[0] or 0
        dates.append(date)
        etats_moyens.append(round(etat_moyen, 1))
    
    conn.close()
    return {
        'dates': dates,
        'etats': etats_moyens
    }

def get_historique_etats_train(train_id, jours=90):
    conn = sqlite3.connect('oncf.db')
    c = conn.cursor()
    
    dates = []
    etats = []
    
    # On suppose qu'on a une table historique_etat_train qui enregistre les changements
    # Pour simplifier, on va générer des données fictives
    for i in range(jours, -1, -1):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        # Simulation d'un état qui fluctue
        etat = 80 + (i % 20) - 10
        dates.append(date)
        etats.append(max(0, min(100, etat)))
    
    conn.close()
    return {
        'dates': dates,
        'etats': etats
    }

def get_anomalies_par_categorie():
    conn = sqlite3.connect('oncf.db')
    c = conn.cursor()
    c.execute("""SELECT categorie, COUNT(*) FROM anomalies 
                 WHERE date_signalement >= date('now', '-3 months')
                 GROUP BY categorie""")
    result = c.fetchall()
    conn.close()
    
    categories = []
    counts = []
    for row in result:
        categories.append(row[0])
        counts.append(row[1])
    
    return {
        'categories': categories,
        'counts': counts
    }

# Initialiser la base de données au premier import
init_db()
