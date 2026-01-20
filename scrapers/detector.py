import requests
from bs4 import BeautifulSoup
from typing import Literal, Optional, Tuple, Dict
import logging

ForumType = Literal["vbulletin", "xenforo", "unknown"]

def detect_forum_type(url: str, cookies: Optional[Dict] = None, user_agent: Optional[str] = None) -> Tuple[ForumType, Optional[str]]:
    """
    Détecte automatiquement le type de forum.
    Retourne (type, message_info)
    """
    try:
        headers = {
            'User-Agent': user_agent or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }

        response = requests.get(url, timeout=15, headers=headers, cookies=cookies)

        if response.status_code == 403:
             return "unknown", "Accès refusé (403). Protection Cloudflare/Bot détectée. Configurez les cookies dans les options avancées."

        html = response.text.lower()
        soup = BeautifulSoup(response.text, 'lxml')

        # Détection XenForo (Prioritaire car plus structuré)
        xenforo_signs = [
            'xenforo' in html,
            'xf-' in html,
            soup.find('html', {'data-app': 'public'}), # Strong signal
            soup.find('div', class_='p-body'),
            soup.find('div', class_='p-pageWrapper'),
            'bbwrapper' in html, # Often used in XF content
        ]

        # Détection vBulletin
        vbulletin_signs = [
            'vbulletin' in html,
            'vb_' in html,
            soup.find('div', class_='vb-postbit'),
            soup.find('div', id='vbulletin_html'),
            soup.find('div', class_='postbit'), # Common in vB
            soup.find('table', class_='tborder'), # vB 3.x classic
            'postcontainer' in html, # vB 4/5
        ]

        if any(xenforo_signs) and soup.find('html', {'data-app': 'public'}):
             return "xenforo", "Forum XenForo détecté (Signature HTML)"

        if any(vbulletin_signs):
            return "vbulletin", "Forum vBulletin détecté"

        if any(xenforo_signs): # Fallback weak detection
             return "xenforo", "Forum XenForo détecté (Indices faibles)"

        return "unknown", "Type de forum non reconnu ou structure inconnue"

    except Exception as e:
        return "unknown", f"Erreur de connexion lors de la détection: {str(e)}"
