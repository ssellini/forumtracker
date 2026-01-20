import streamlit as st
from services.analyzer import AnalyzerService

st.set_page_config(page_title="Analyse IA", page_icon="🤖")

st.title("🤖 Analyse IA (Gemini)")

if "scraped_data" not in st.session_state or not st.session_state.scraped_data:
    st.warning("Pas de données.")
    st.stop()

# Check API Key
if not st.session_state.get("api_key"):
    st.error("⚠️ Clé API Gemini manquante. Configurez-la dans le menu latéral ou .streamlit/secrets.toml")
    st.stop()

# Prepare Data
all_posts = []
for pid, posts in st.session_state.scraped_data.items():
    all_posts.extend(posts)

translated_count = sum(1 for p in all_posts if p.get('content_translated'))
st.info(f"📊 {len(all_posts)} messages chargés ({translated_count} traduits) prêts pour analyse.")

if translated_count == 0:
    st.warning("⚠️ Attention : Aucune traduction trouvée. L'analyse se fera sur le texte original (risque de moins bonne qualité si Gemini ne gère pas bien le mélange de langues).")

# Options
st.subheader("🎯 Configuration de l'analyse")

opts_col1, opts_col2 = st.columns(2)
with opts_col1:
    opt_summary = st.checkbox("Résumé global", value=True)
    opt_points = st.checkbox("Points clés", value=True)
with opts_col2:
    opt_sentiment = st.checkbox("Sentiment général", value=True)
    opt_questions = st.checkbox("Questions/Problèmes soulevés", value=False)

custom_instr = st.text_area("📝 Instructions supplémentaires (optionnel)", placeholder="Ex: Focus sur les avis négatifs concernant la livraison...")

if st.button("🤖 Lancer l'analyse", type="primary"):
    analyzer = AnalyzerService(st.session_state.api_key)

    # Build Instruction String
    instructions = []
    if opt_summary: instructions.append("- Fais un résumé global de la discussion.")
    if opt_points: instructions.append("- Liste les points clés abordés sous forme de bullet points.")
    if opt_sentiment: instructions.append("- Analyse le sentiment général (Positif/Négatif/Neutre) avec justification.")
    if opt_questions: instructions.append("- Identifie les questions ou problèmes techniques soulevés par les utilisateurs.")
    if custom_instr: instructions.append(f"- INSTRUCTION SPECIALE : {custom_instr}")

    full_instruction = "\n".join(instructions)

    # Format Content
    formatted_content = AnalyzerService.format_posts_for_analysis(all_posts)

    with st.spinner("Gemini analyse les discussions..."):
        result = analyzer.analyze_posts(formatted_content, full_instruction)

    if result:
        st.session_state.analysis_results["last_run"] = result
        st.success("Analyse terminée !")
    else:
        st.error("Erreur lors de l'analyse.")

# Display Result
if "analysis_results" in st.session_state and "last_run" in st.session_state.analysis_results:
    st.divider()
    st.subheader("📊 Résultats de l'analyse")
    st.markdown(st.session_state.analysis_results["last_run"])

    # Save/Download logic could be here or in Historique
    st.download_button(
        "💾 Télécharger le rapport",
        data=st.session_state.analysis_results["last_run"],
        file_name="rapport_analyse.md",
        mime="text/markdown"
    )
