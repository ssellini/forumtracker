import streamlit as st
from services.storage import StorageService
import json

st.set_page_config(page_title="Historique", page_icon="📚")

st.title("📚 Historique & Sauvegardes")

# --- Import ---
st.subheader("📂 Charger une sauvegarde")
uploaded_file = st.file_uploader("Glisser un fichier JSON ici (Export complet)", type=["json"])

if uploaded_file:
    try:
        content = json.load(uploaded_file)
        if st.button("Restaurer cette sauvegarde"):
            # Restore everything
            if "sources" in content: st.session_state.sources = content["sources"]
            if "scraped_data" in content: st.session_state.scraped_data = content["scraped_data"]
            if "analysis_results" in content: st.session_state.analysis_results = content["analysis_results"]
            st.success("Session restaurée avec succès !")
            st.rerun()
    except Exception as e:
        st.error(f"Erreur de lecture du fichier : {e}")

st.divider()

# --- Export ---
st.subheader("💾 Sauvegarder la session actuelle")

# Prepare Full Dump
full_dump = {
    "sources": st.session_state.get("sources", []),
    "scraped_data": st.session_state.get("scraped_data", {}),
    "analysis_results": st.session_state.get("analysis_results", {})
}

json_str = StorageService.export_to_json(full_dump)

col1, col2 = st.columns(2)
with col1:
    st.info(f"""
    **Statistiques Session :**
    - Sources : {len(full_dump['sources'])}
    - Sujets extraits : {len(full_dump['scraped_data'])}
    - Analyse disponible : {"Oui" if full_dump['analysis_results'] else "Non"}
    """)

with col2:
    st.download_button(
        "📥 Télécharger Sauvegarde Complète",
        data=json_str,
        file_name="forum_tracker_full_backup.json",
        mime="application/json",
        help="Contient sources, messages extraits et analyses."
    )

# --- Preview Data ---
st.divider()
with st.expander("👁️ Aperçu des données brutes (JSON)"):
    st.json(full_dump)
