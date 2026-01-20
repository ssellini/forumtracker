import streamlit as st
from services.storage import StorageService

st.set_page_config(
    page_title="Forum Tracker",
    page_icon="🕵️",
    layout="wide",
    initial_sidebar_state="expanded"
)

def init_session_state():
    if "sources" not in st.session_state:
        st.session_state.sources = [] # List of Topic objects (dicts)
    if "scraped_data" not in st.session_state:
        st.session_state.scraped_data = {} # {topic_id: [posts]}
    if "analysis_results" not in st.session_state:
        st.session_state.analysis_results = {}
    if "api_key" not in st.session_state:
        # Try load from secrets
        try:
            st.session_state.api_key = st.secrets["GEMINI_API_KEY"]
        except:
            st.session_state.api_key = ""

init_session_state()

st.title("🕵️ Forum Tracker")
st.markdown("""
### Bienvenue sur Forum Tracker

Cette application permet de suivre, traduire et analyser des discussions de forums étrangers (vBulletin / XenForo).

#### Workflow :
1. **🔗 Gestion Sources** : Ajoutez les URLs des sujets à suivre.
2. **📥 Extraction** : Scrapez les nouveaux messages.
3. **🌐 Traduction** : Traduisez le contenu (Espagnol -> Français).
4. **🤖 Analyse IA** : Utilisez Gemini pour synthétiser les discussions.
5. **📚 Historique** : Sauvegardez et rechargez vos sessions.

👈 Commencez par configurer vos sources dans le menu de gauche.
""")

# Sidebar Global Settings
with st.sidebar:
    st.header("⚙️ Configuration")

    # API Key Management
    if not st.session_state.api_key:
        api_input = st.text_input("Clé API Gemini", type="password", help="Requise pour l'analyse IA")
        if api_input:
            st.session_state.api_key = api_input
            st.success("Clé enregistrée !")
    else:
        st.success("✅ API Key active")
        if st.button("Changer clé API"):
            st.session_state.api_key = ""
            st.rerun()

    st.markdown("---")
    st.info("Version 1.0.0")
