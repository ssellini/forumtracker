import streamlit as st
from services.translator import TranslationService

st.set_page_config(page_title="Traduction", page_icon="🌐")

st.title("🌐 Traduction ES → FR")

if "scraped_data" not in st.session_state or not st.session_state.scraped_data:
    st.warning("Aucune donnée extraite à traduire. Veuillez passer par l'étape d'extraction.")
    st.stop()

total_posts = sum(len(p) for p in st.session_state.scraped_data.values())
st.info(f"{total_posts} messages chargés prêts à être traduits.")

col1, col2 = st.columns(2)
with col1:
    src_lang = st.selectbox("Langue source", ["es", "en", "de"], index=0)
with col2:
    target_lang = st.selectbox("Langue cible", ["fr", "en"], index=0)

if st.button("🌐 Lancer la traduction", type="primary"):
    translator = TranslationService(source=src_lang, target=target_lang)

    prog_bar = st.progress(0)
    status = st.empty()

    current_count = 0

    # Iterate all sources
    for source_id, posts in st.session_state.scraped_data.items():
        # Define a callback that updates global progress
        def batch_cb(done, total):
            pass # We handle global progress manually below

        # We process one by one to update global bar
        for i, post in enumerate(posts):
            if not post.get('content_translated'):
                post['content_translated'] = translator.translate_text(post.get('content_original', ''))

            current_count += 1
            prog_bar.progress(current_count / total_posts)
            status.text(f"Traduction : {current_count}/{total_posts}")

    status.success("✅ Traduction terminée !")
    st.rerun()

# --- Affichage Résultats ---
st.divider()
st.subheader("📋 Résultats")

tabs = st.tabs([s['name'] for s in st.session_state.sources if s['id'] in st.session_state.scraped_data])

for i, tab in enumerate(tabs):
    source = [s for s in st.session_state.sources if s['id'] in st.session_state.scraped_data][i]
    posts = st.session_state.scraped_data[source['id']]

    with tab:
        for post in posts:
            with st.container(border=True):
                c1, c2 = st.columns([1, 4])
                with c1:
                    st.caption(f"👤 {post.get('author')}")
                    st.caption(f"📅 {post.get('date')}")
                with c2:
                    if post.get('content_translated'):
                        st.markdown(f"🇫🇷 {post.get('content_translated')}")
                        with st.expander("Voir original 🇪🇸"):
                            st.text(post.get('content_original'))
                    else:
                        st.text(post.get('content_original'))
                        st.caption("⚠️ Non traduit")

st.divider()
if st.button("➡️ Passer à l'analyse IA"):
    st.switch_page("pages/4_🤖_Analyse_IA.py")
