from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from datetime import datetime, timedelta
import database as db
import math

app = Flask(__name__)
app.secret_key = 'oncf_secret_key_123'

# Constantes
CRITICITE_MAX_GLOBALE = 100  # Score max pour le calcul de l'état de santé
ANOMALIES_PERIODE_JOURS = 90  # Période en jours pour le calcul de l'état de santé

# Fonctions utilitaires
def calculer_criticite(gravite, criticite_composant, frequence_pannes):
    """Calcule la criticité d'une anomalie"""
    # Pondération: gravité (50%), criticité composant (30%), fréquence (20%)
    score = (gravite * 0.5) + (criticite_composant * 0.3) + (min(frequence_pannes, 10) * 2)
    return min(score, 100)

def calculer_etat_sante(train_id):
    """Calcule l'état de santé d'un train"""
    anomalies = db.get_anomalies_recentes(train_id, ANOMALIES_PERIODE_JOURS)
    if not anomalies:
        return 100
    
    total_criticite = sum(anomalie['criticite_calculée'] for anomalie in anomalies)
    etat_sante = 100 - (total_criticite / (CRITICITE_MAX_GLOBALE * len(anomalies))) * 100
    return max(0, min(100, round(etat_sante, 1)))

def get_categorie_etat(etat_sante):
    """Retourne la catégorie d'état du train"""
    if etat_sante < 50:
        return ('🔴 Mauvais', 'danger')
    elif 50 <= etat_sante < 80:
        return ('🟡 Moyen', 'warning')
    else:
        return ('🟢 Bon', 'success')

# Routes
@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if session['role'] == 'technicien':
        return redirect(url_for('accueil_technicien'))
    else:
        return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = db.authentifier_utilisateur(email, password)
        if user:
            session['user_id'] = user['id']
            session['nom'] = user['nom']
            session['role'] = user['role']
            return redirect(url_for('home'))
        else:
            flash('Email ou mot de passe incorrect', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/technicien')
def accueil_technicien():
    if 'user_id' not in session or session['role'] != 'technicien':
        return redirect(url_for('login'))
    
    anomalies = db.get_anomalies_technicien(session['user_id'], limit=3)
    return render_template('technicien.html', anomalies=anomalies)

@app.route('/anomalie/nouvelle', methods=['GET', 'POST'])
def nouvelle_anomalie():
    if 'user_id' not in session or session['role'] != 'technicien':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        train_id = request.form['train']
        categorie = request.form['categorie']
        composant = request.form['composant']
        description = request.form['description']
        gravite = int(request.form['gravite'])
        
        # Récupérer les données pour le calcul
        criticite_composant = db.get_criticite_composant(composant)
        frequence_pannes = db.get_frequence_pannes(train_id, composant)
        
        # Calculer la criticité
        criticite = calculer_criticite(gravite, criticite_composant, frequence_pannes)
        
        # Déterminer l'urgence
        if criticite >= 70:
            urgence = 'Urgent'
        elif 30 <= criticite < 70:
            urgence = 'Moyen'
        else:
            urgence = 'Faible'
        
        # Enregistrer l'anomalie
        db.ajouter_anomalie(
            train_id=train_id,
            technicien_id=session['user_id'],
            categorie=categorie,
            composant=composant,
            description=description,
            criticite_calculée=criticite,
            urgence=urgence
        )
        
        # Mettre à jour l'état du train
        etat_sante = calculer_etat_sante(train_id)
        db.mettre_a_jour_etat_train(train_id, etat_sante)
        
        flash('Anomalie enregistrée avec succès', 'success')
        return redirect(url_for('accueil_technicien'))
    
    trains = db.get_trains()
    composants = db.get_composants_par_categorie()
    return render_template('nouvelle_anomalie.html', trains=trains, composants=composants)

@app.route('/anomalies')
def liste_anomalies():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    statut = request.args.get('statut', 'tous')
    urgence = request.args.get('urgence', 'tous')
    
    if session['role'] == 'technicien':
        anomalies = db.get_anomalies_technicien(session['user_id'], statut=statut, urgence=urgence)
    else:
        anomalies = db.get_anomalies(statut=statut, urgence=urgence)
    
    return render_template('anomalies.html', anomalies=anomalies, statut=statut, urgence=urgence)

@app.route('/conformite/nouvelle', methods=['GET', 'POST'])
def nouvelle_conformite():
    if 'user_id' not in session or session['role'] != 'technicien':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        train_id = request.form['train']
        type_intervention = request.form['type_intervention']
        composant = request.form['composant']
        piece_remplacee = request.form['piece_remplacee']
        resultat = request.form['resultat']
        observations = request.form['observations']
        
        # Enregistrer la fiche de conformité
        db.ajouter_conformite(
            train_id=train_id,
            technicien_id=session['user_id'],
            type_intervention=type_intervention,
            composant=composant,
            piece_remplacee=piece_remplacee,
            resultat=resultat,
            observations=observations
        )
        
        # Mettre à jour l'état du train
        etat_sante = calculer_etat_sante(train_id)
        db.mettre_a_jour_etat_train(train_id, etat_sante)
        
        # Marquer les anomalies associées comme résolues
        db.marquer_anomalies_resolues(train_id, composant)
        
        flash('Fiche de conformité enregistrée', 'success')
        return redirect(url_for('accueil_technicien'))
    
    trains = db.get_trains()
    pieces = db.get_pieces()
    return render_template('conformite.html', trains=trains, pieces=pieces)

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session or session['role'] != 'responsable':
        return redirect(url_for('login'))
    
    # KPIs
    trains = db.get_trains()
    etats = [get_categorie_etat(train['etat_sante']) for train in trains]
    kpi_mauvais = sum(1 for etat in etats if etat[1] == 'danger')
    kpi_moyen = sum(1 for etat in etats if etat[1] == 'warning')
    kpi_bon = sum(1 for etat in etats if etat[1] == 'success')
    
    anomalies_en_cours = db.get_anomalies(statut='en_cours')
    
    # Données pour les graphiques
    historique_etats = db.get_historique_etats(30)  # 30 derniers jours
    anomalies_par_categorie = db.get_anomalies_par_categorie()
    
    return render_template('dashboard.html',
                         kpi_mauvais=kpi_mauvais,
                         kpi_moyen=kpi_moyen,
                         kpi_bon=kpi_bon,
                         anomalies_en_cours=len(anomalies_en_cours),
                         trains=trains,
                         historique_etats=historique_etats,
                         anomalies_par_categorie=anomalies_par_categorie)

@app.route('/pieces')
def gestion_pieces():
    if 'user_id' not in session or session['role'] != 'responsable':
        return redirect(url_for('login'))
    
    pieces = db.get_pieces()
    return render_template('pieces.html', pieces=pieces)

@app.route('/api/etat_sante/<train_id>')
def api_etat_sante(train_id):
    historique = db.get_historique_etats_train(train_id, 90)
    return jsonify(historique)

if __name__ == '__main__':
    app.run(debug=True)
