import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# Configuration de la page
st.set_page_config(
    page_title="ONCF Maintenance Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Mock database functions (à remplacer par vos vraies fonctions)
class DB:
    @staticmethod
    def get_trains():
        return [{"id": 1, "nom": "Train 1", "etat_sante": 75}, 
                {"id": 2, "nom": "Train 2", "etat_sante": 45}]

    @staticmethod
    def get_anomalies(technicien_id=None, statut='tous', urgence='tous'):
        data = [
            {"id": 1, "train": "Train 1", "composant": "Moteur", "description": "Surchauffe", "criticite": 80, "urgence": "Urgent", "statut": "en_cours"},
            {"id": 2, "train": "Train 2", "composant": "Freins", "description": "Usure", "criticite": 60, "urgence": "Moyen", "statut": "en_cours"}
        ]
        return data

    @staticmethod
    def ajouter_anomalie(train_id, technicien_id, categorie, composant, description, criticite_calculée, urgence):
        # Implémentez votre logique d'ajout ici
        pass

# Authentification
def authenticate(username, password):
    # À remplacer par votre logique d'authentification réelle
    users = {
        "technicien": {"password": "tech123", "role": "technicien"},
        "responsable": {"password": "resp123", "role": "responsable"}
    }
    return users.get(username, {}).get("password") == password, users.get(username, {}).get("role")

# Initialisation de session
if 'auth' not in st.session_state:
    st.session_state.auth = False
    st.session_state.role = None
    st.session_state.user_id = None

# Page de connexion
if not st.session_state.auth:
    st.title("Connexion ONCF")
    
    with st.form("login_form"):
        username = st.text_input("Nom d'utilisateur")
        password = st.text_input("Mot de passe", type="password")
        
        if st.form_submit_button("Se connecter"):
            auth_success, role = authenticate(username, password)
            if auth_success:
                st.session_state.auth = True
                st.session_state.role = role
                st.session_state.user_id = username
                st.rerun()
            else:
                st.error("Identifiants incorrects")

# Interface après connexion
else:
    # Menu sidebar
    st.sidebar.title(f"Bonjour, {st.session_state.user_id}")
    st.sidebar.button("Déconnexion", on_click=lambda: st.session_state.clear())
    
    if st.session_state.role == "technicien":
        st.sidebar.subheader("Menu Technicien")
        page = st.sidebar.radio("Navigation", ["Accueil", "Nouvelle Anomalie", "Fiche de Conformité", "Mes Anomalies"])
    else:
        st.sidebar.subheader("Menu Responsable")
        page = st.sidebar.radio("Navigation", ["Dashboard", "Gestion des Anomalies", "Gestion des Pièces"])

    # Pages Technicien
    if st.session_state.role == "technicien":
        if page == "Accueil":
            st.title("Tableau de bord technicien")
            anomalies = DB.get_anomalies(technicien_id=st.session_state.user_id)
            st.dataframe(pd.DataFrame(anomalies))

        elif page == "Nouvelle Anomalie":
            st.title("Déclarer une anomalie")
            
            with st.form("anomalie_form"):
                trains = DB.get_trains()
                train_options = {train['id']: train['nom'] for train in trains}
                train_id = st.selectbox("Train concerné", options=list(train_options.keys()), format_func=lambda x: train_options[x])
                
                col1, col2 = st.columns(2)
                categorie = col1.selectbox("Catégorie", ["Mécanique", "Electrique", "Système"])
                composant = col2.selectbox("Composant", ["Moteur", "Freins", "Système électrique"])
                
                description = st.text_area("Description de l'anomalie")
                gravite = st.slider("Gravité (1-10)", 1, 10, 5)
                
                if st.form_submit_button("Enregistrer"):
                    # Calcul de criticité (exemple simplifié)
                    criticite = gravite * 10
                    urgence = "Urgent" if criticite >= 70 else ("Moyen" if criticite >= 40 else "Faible")
                    
                    DB.ajouter_anomalie(
                        train_id=train_id,
                        technicien_id=st.session_state.user_id,
                        categorie=categorie,
                        composant=composant,
                        description=description,
                        criticite_calculée=criticite,
                        urgence=urgence
                    )
                    st.success("Anomalie enregistrée avec succès")

        elif page == "Fiche de Conformité":
            st.title("Fiche de conformité d'intervention")
            # Implémentez similaire à Nouvelle Anomalie

        elif page == "Mes Anomalies":
            st.title("Mes anomalies en cours")
            anomalies = DB.get_anomalies(technicien_id=st.session_state.user_id)
            st.dataframe(pd.DataFrame(anomalies))

    # Pages Responsable
    else:
        if page == "Dashboard":
            st.title("Tableau de bord responsable")
            
            # KPI Cards
            col1, col2, col3 = st.columns(3)
            col1.metric("Trains en bon état", "15", "2% vs hier")
            col2.metric("Anomalies urgentes", "3", "-1% vs hier")
            col3.metric("Interventions aujourd'hui", "7", "3 nouvelles")
            
            # Graphiques
            st.subheader("État du parc matériel")
            fig = px.pie(values=[15, 5, 3], names=["Bon état", "État moyen", "Mauvais état"])
            st.plotly_chart(fig, use_container_width=True)

        elif page == "Gestion des Anomalies":
            st.title("Gestion des anomalies")
            
            col1, col2 = st.columns(2)
            statut = col1.selectbox("Statut", ["tous", "en_cours", "résolu"])
            urgence = col2.selectbox("Urgence", ["tous", "Urgent", "Moyen", "Faible"])
            
            anomalies = DB.get_anomalies(statut=statut, urgence=urgence)
            st.dataframe(pd.DataFrame(anomalies))

        elif page == "Gestion des Pièces":
            st.title("Gestion des pièces détachées")
            # Implémentez selon vos besoins

# Pour lancer l'application : streamlit run app.py
