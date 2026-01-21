import requests
from bs4 import BeautifulSoup
from typing import Literal, Optional, Tuple, Dict
from urllib.parse import urlparse
import logging
import time
import random

ForumType = Literal["vbulletin", "xenforo", "unknown"]

# User-Agents réalistes
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0',
]

def detect_forum_type(url: str, cookies: Optional[Dict] = None, user_agent: Optional[str] = None) -> Tuple[ForumType, Optional[str]]:
    """
    Détecte automatiquement le type de forum.
    Retourne (type, message_info)
    """
    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    headers = {
        'User-Agent': user_agent or random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Sec-Ch-Ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Referer': base_url,
    }

    max_retries = 3
    retry_delays = [2, 5, 10]

    try:
        response = None
        for attempt in range(max_retries + 1):
            try:
                response = requests.get(url, timeout=15, headers=headers, cookies=cookies)

                if response.status_code == 403:
                    if attempt < max_retries:
                        delay = retry_delays[attempt]
                        logging.warning(f"Détection: 403 reçu, retry {attempt + 1}/{max_retries} dans {delay}s...")
                        time.sleep(delay)
                        headers['User-Agent'] = random.choice(USER_AGENTS)
                        continue
                    else:
                        return "unknown", (
                            "Accès refusé (403) après plusieurs tentatives. Protection anti-bot détectée.\n"
                            "Solutions:\n"
                            "1. Ajoutez des cookies Cloudflare (cf_clearance) dans les options avancées\n"
                            "2. Utilisez l'extension 'Cookie-Editor' pour exporter les cookies\n"
                            "3. Attendez quelques minutes et réessayez"
                        )
                break
            except requests.RequestException as e:
                if attempt < max_retries:
                    time.sleep(retry_delays[attempt])
                    continue
                raise

        if response is None:
            return "unknown", "Impossible de se connecter après plusieurs tentatives."

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
