from deep_translator import GoogleTranslator
from typing import List
import time
import logging

class TranslationService:

    def __init__(self, source: str = 'es', target: str = 'fr'):
        self.translator = GoogleTranslator(source=source, target=target)

    def translate_text(self, text: str) -> str:
        if not text or len(text.strip()) < 2:
            return text

        try:
            # Split if text is too long (Google Translate limit is usually 5000 chars)
            if len(text) > 4500:
                chunks = [text[i:i+4500] for i in range(0, len(text), 4500)]
                translated_chunks = []
                for chunk in chunks:
                    translated_chunks.append(self.translator.translate(chunk))
                    time.sleep(0.5)
                return " ".join(translated_chunks)
            else:
                return self.translator.translate(text)
        except Exception as e:
            logging.error(f"Translation error: {e}")
            return f"[Erreur traduction] {text[:50]}..."

    def translate_posts(self, posts: List[dict], progress_callback=None) -> List[dict]:
        """
        Traduit une liste de posts (dictionnaires).
        Modifie les dictionnaires en place ou retourne une copie.
        """
        total = len(posts)
        for i, post in enumerate(posts):
            if not post.get('content_translated'): # Avoid re-translating
                original = post.get('content_original', '')
                post['content_translated'] = self.translate_text(original)

            if progress_callback:
                progress_callback(i + 1, total)

            # Petit délai pour être gentil avec l'API gratuite
            # time.sleep(0.2)

        return posts
