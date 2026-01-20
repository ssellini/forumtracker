import google.generativeai as genai
import logging
from typing import Optional

class AnalyzerService:

    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("API Key is missing")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def analyze_posts(self, posts_text: str, instructions: str) -> Optional[str]:
        """
        Envoie les posts à Gemini pour analyse.
        """
        try:
            # Construct prompt
            prompt = f"""
            Tu es un expert en analyse de discussions de forums.
            Voici une série de messages extraits d'un forum (traduits en français).

            TACHE:
            {instructions}

            CONTENU A ANALYSER:
            {posts_text[:30000]}  # Limit context window safety check
            """

            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logging.error(f"Gemini Analysis Error: {e}")
            return f"Erreur lors de l'analyse : {str(e)}"

    @staticmethod
    def format_posts_for_analysis(posts: list) -> str:
        """Helper to format posts into a string buffer"""
        buffer = []
        for p in posts:
            author = p.get('author', 'Inconnu')
            date = p.get('date', '')
            content = p.get('content_translated') or p.get('content_original', '')
            buffer.append(f"--- Message de {author} le {date} ---\n{content}\n")
        return "\n".join(buffer)
