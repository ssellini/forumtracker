import streamlit as st
import uuid
import json
from scrapers.detector import detect_forum_type
from services.storage import StorageService
from models.topic import Topic

st.set_page_config(page_title="Gestion Sources", page_icon="🔗")

st.title("🔗 Gestion des Sources")

# --- Formulaire Ajout ---
with st.expander("➕ Ajouter une nouvelle source", expanded=True):
    with st.form("add_source_form"):
        col1, col2 = st.columns([1, 2])
        with col1:
            name = st.text_input("Nom du sujet (Reference)", placeholder="Ex: Sujet ABC")
        with col2:
            url = st.text_input("URL du sujet", placeholder="https://forum.com/threads/...")

        type_choice = st.radio("Type de forum", ["Auto-detect", "vBulletin", "XenForo"], horizontal=True)

        # Options Avancées (Cookies pour Cloudflare)
        with st.expander("⚙️ Options Avancées (Cookies / Headers)"):
            st.markdown("""
            **Contournement Cloudflare :** Si le site est protégé, copiez vos cookies ici (Format JSON).
            Utilisez une extension comme 'Cookie-Editor' pour exporter les cookies en JSON.
            """)
            cookies_json = st.text_area("Cookies (JSON)", placeholder='[{"name": "cf_clearance", "value": "..."}, ...]')
            user_agent = st.text_input("User-Agent Spécifique", placeholder="Laissez vide pour défaut")

        submitted = st.form_submit_button("Ajouter & Tester")

        if submitted:
            if not name or not url:
                st.error("Le nom et l'URL sont obligatoires.")
            else:
                # Parse Cookies
                cookies_dict = {}
                if cookies_json:
                    try:
                        raw_cookies = json.loads(cookies_json)
                        # Handle list of dicts (Cookie-Editor format) or simple dict
                        if isinstance(raw_cookies, list):
                            for c in raw_cookies:
                                if 'name' in c and 'value' in c:
                                    cookies_dict[c['name']] = c['value']
                        elif isinstance(raw_cookies, dict):
                            cookies_dict = raw_cookies
                    except json.JSONDecodeError:
                        st.warning("Format JSON des cookies invalide. Ignoré.")

                # Detection / Test
                status_msg = st.empty()
                status_msg.info("⏳ Test de connexion en cours...")

                detected_type = "unknown"
                if type_choice == "Auto-detect":
                    d_type, d_msg = detect_forum_type(url, cookies=cookies_dict, user_agent=user_agent)
                    if d_type != "unknown":
                        detected_type = d_type
                        st.success(f"✅ {d_msg}")
                    else:
                        st.warning(f"⚠️ {d_msg}")
                        detected_type = "auto" # Keep auto if failed, or let user force it
                else:
                    detected_type = type_choice.lower()
                    # Just test reachability
                    d_type, d_msg = detect_forum_type(url, cookies=cookies_dict, user_agent=user_agent)
                    if d_msg.startswith("Accès refusé"):
                        st.error(f"❌ {d_msg}")
                    else:
                        st.success(f"✅ Connexion réussie ({d_msg})")

                # Save
                new_topic = {
                    "id": str(uuid.uuid4()),
                    "name": name,
                    "url": url,
                    "forum_type": detected_type,
                    "cookies": cookies_dict,
                    "user_agent": user_agent
                }

                if "sources" not in st.session_state:
                    st.session_state.sources = []
                st.session_state.sources.append(new_topic)
                st.success("Source ajoutée avec succès !")
                st.rerun()

# --- Liste Sources ---
st.divider()
st.subheader("📋 Sources configurées")

if "sources" not in st.session_state or not st.session_state.sources:
    st.info("Aucune source configurée.")
else:
    for idx, source in enumerate(st.session_state.sources):
        with st.container(border=True):
            c1, c2, c3 = st.columns([4, 2, 1])
            with c1:
                st.markdown(f"**{source['name']}**")
                st.caption(f"{source['url']}")
            with c2:
                st.code(f"Type: {source['forum_type']}")
                if source.get('cookies'):
                    st.caption("🍪 Cookies configurés")
            with c3:
                if st.button("🗑️", key=f"del_{source['id']}"):
                    st.session_state.sources.pop(idx)
                    st.rerun()

# --- Export/Import ---
st.divider()
c_exp, c_imp = st.columns(2)

with c_exp:
    if st.session_state.get("sources"):
        json_str = StorageService.export_to_json(st.session_state.sources)
        st.download_button(
            "💾 Exporter Config",
            data=json_str,
            file_name="forum_sources_config.json",
            mime="application/json"
        )

with c_imp:
    uploaded_file = st.file_uploader("📂 Importer Config", type=["json"])
    if uploaded_file:
        content = uploaded_file.read().decode()
        data = StorageService.import_from_json(content)
        if isinstance(data, list):
            if st.button("Confirmer l'import (Écrase l'existant)"):
                st.session_state.sources = data
                st.success("Configuration importée !")
                st.rerun()
        else:
            st.error("Format de fichier invalide.")
