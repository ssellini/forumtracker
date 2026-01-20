import streamlit as st
from datetime import datetime, timedelta
import time
from scrapers.vbulletin import VBulletinScraper
from scrapers.xenforo import XenForoScraper
from models.post import Post

st.set_page_config(page_title="Extraction", page_icon="📥")

st.title("📥 Extraction des Messages")

if "sources" not in st.session_state or not st.session_state.sources:
    st.warning("Veuillez d'abord configurer des sources.")
    st.stop()

# --- Configuration Extraction ---
with st.container(border=True):
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📅 Période")
        period_mode = st.radio("Mode", ["Raccourci", "Personnalisé"], horizontal=True)

        since_date = datetime.now()

        if period_mode == "Raccourci":
            delta = st.selectbox("Récupérer les messages depuis :",
                options=["24h", "7 jours", "30 jours", "Toujours"],
                index=1
            )
            if delta == "24h": since_date -= timedelta(days=1)
            elif delta == "7 jours": since_date -= timedelta(days=7)
            elif delta == "30 jours": since_date -= timedelta(days=30)
            elif delta == "Toujours": since_date = datetime(2000, 1, 1)
        else:
            d = st.date_input("Date de début", value=datetime.now() - timedelta(days=7))
            since_date = datetime.combine(d, datetime.min.time())

    with col2:
        st.subheader("📋 Sources & Options")
        selected_sources_names = st.multiselect(
            "Sources à extraire",
            options=[s['name'] for s in st.session_state.sources],
            default=[s['name'] for s in st.session_state.sources]
        )

        max_pages = st.number_input("Max pages par sujet", min_value=1, value=5)
        delay = st.number_input("Délai entre requêtes (sec)", min_value=0.5, value=1.5, step=0.5)

# --- Runner ---
if st.button("🚀 Lancer l'extraction", type="primary"):
    selected_sources = [s for s in st.session_state.sources if s['name'] in selected_sources_names]

    st.session_state.scraped_data = {} # Reset current extraction

    total_sources = len(selected_sources)
    overall_progress = st.progress(0)
    status_text = st.empty()

    for idx, source in enumerate(selected_sources):
        status_text.markdown(f"**Traitement de : {source['name']}...**")

        # Init Scraper
        scraper = None
        ftype = source['forum_type']

        # Auto-resolve if needed (simple heuristic if logic in detector failed or wasn't run)
        if ftype == 'auto':
            if 'xenforo' in source['url'] or 'threads' in source['url']: ftype = 'xenforo'
            else: ftype = 'vbulletin'

        cookies = source.get('cookies')
        ua = source.get('user_agent')

        if ftype == 'xenforo':
            scraper = XenForoScraper(delay=delay, cookies=cookies, user_agent=ua)
        else:
            scraper = VBulletinScraper(delay=delay, cookies=cookies, user_agent=ua)

        # Progress for this source
        p_bar = st.progress(0)
        p_text = st.empty()

        def progress_cb(page, total):
            pct = min(page / total, 1.0) if total else 0
            p_bar.progress(pct)
            p_text.text(f"Page {page}/{total if total else '?'}")

        posts = []
        generator = scraper.scrape_all_pages(
            base_url=source['url'],
            topic_id=source['id'],
            since_date=since_date,
            max_pages=max_pages,
            progress_callback=progress_cb
        )

        for item in generator:
            if "error" in item:
                st.error(f"[{source['name']}] {item['error']}")
            else:
                posts.append(item)

        # Store results
        if posts:
            st.session_state.scraped_data[source['id']] = posts

        overall_progress.progress((idx + 1) / total_sources)
        p_text.empty()
        p_bar.empty()

    status_text.success("✅ Extraction terminée !")
    time.sleep(1)
    st.rerun()

# --- Résultats ---
if st.session_state.get("scraped_data"):
    st.divider()
    st.subheader(f"Résultats ({sum(len(p) for p in st.session_state.scraped_data.values())} messages)")

    tabs = st.tabs([s['name'] for s in st.session_state.sources if s['id'] in st.session_state.scraped_data])

    for i, tab in enumerate(tabs):
        source = [s for s in st.session_state.sources if s['id'] in st.session_state.scraped_data][i]
        posts = st.session_state.scraped_data[source['id']]

        with tab:
            st.caption(f"{len(posts)} messages trouvés")
            for post in posts[:10]: # Show first 10 preview
                with st.expander(f"{post.get('author')} - {post.get('date')}"):
                    st.text(post.get('content_original'))
            if len(posts) > 10:
                st.info(f"... et {len(posts)-10} autres messages.")

    col1, col2 = st.columns(2)
    with col1:
        pass # Save button logic could go here or in Historique
    with col2:
        if st.button("➡️ Passer à la traduction"):
            st.switch_page("pages/3_🌐_Traduction.py")
