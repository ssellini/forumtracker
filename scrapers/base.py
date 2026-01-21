from abc import ABC, abstractmethod
from typing import List, Optional, Generator, Dict
from datetime import datetime
from urllib.parse import urlparse
import time
import random
import requests
from bs4 import BeautifulSoup
import logging
import urllib3

# Désactiver les warnings SSL pour le scraping
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class BaseScraper(ABC):
    """Classe abstraite pour les scrapers de forums"""

    # User-Agents réalistes et récents (Chrome, Firefox, Edge)
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
    ]

    DEFAULT_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7,es;q=0.6',
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
        'Cache-Control': 'max-age=0',
    }

    MAX_RETRIES = 3
    RETRY_DELAYS = [2, 5, 10]  # Délais en secondes pour retry

    def __init__(self, delay: float = 1.5, cookies: Optional[Dict] = None, user_agent: Optional[str] = None):
        self.delay = delay
        self.session = requests.Session()
        self.base_domain = None  # Pour le Referer dynamique

        # Update headers
        headers = self.DEFAULT_HEADERS.copy()
        if user_agent:
            headers['User-Agent'] = user_agent
        else:
            # Sélectionner un User-Agent aléatoire pour plus de réalisme
            headers['User-Agent'] = random.choice(self.USER_AGENTS)
        self.session.headers.update(headers)

        # Set cookies if provided
        if cookies:
            self.session.cookies.update(cookies)

    def _set_referer(self, url: str) -> None:
        """Configure le header Referer basé sur l'URL cible"""
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        self.session.headers['Referer'] = base_url
        self.session.headers['Origin'] = base_url
        # Mettre à jour Sec-Fetch-Site pour indiquer same-origin après la première requête
        if self.base_domain == parsed.netloc:
            self.session.headers['Sec-Fetch-Site'] = 'same-origin'
        else:
            self.base_domain = parsed.netloc

    def _make_request_with_retry(self, url: str, timeout: int = 15) -> Optional[requests.Response]:
        """
        Effectue une requête HTTP avec retry et backoff exponentiel pour les erreurs 403.
        Retourne la Response ou None si échec après tous les retries.
        """
        self._set_referer(url)

        for attempt in range(self.MAX_RETRIES + 1):
            try:
                # verify=False pour éviter les erreurs SSL sur certains sites
                response = self.session.get(url, timeout=timeout, verify=False)

                if response.status_code == 403:
                    if attempt < self.MAX_RETRIES:
                        delay = self.RETRY_DELAYS[attempt]
                        logging.warning(f"403 reçu, retry {attempt + 1}/{self.MAX_RETRIES} dans {delay}s...")
                        time.sleep(delay)
                        # Changer de User-Agent pour le retry
                        self.session.headers['User-Agent'] = random.choice(self.USER_AGENTS)
                        continue
                    else:
                        return response  # Retourner le 403 après tous les retries

                return response

            except requests.RequestException as e:
                if attempt < self.MAX_RETRIES:
                    delay = self.RETRY_DELAYS[attempt]
                    logging.warning(f"Erreur requête: {e}, retry dans {delay}s...")
                    time.sleep(delay)
                    continue
                raise

        return None

    @abstractmethod
    def get_page_url(self, base_url: str, page_num: int) -> str:
        """Construit l'URL pour une page donnée"""
        pass

    @abstractmethod
    def get_total_pages(self, soup: BeautifulSoup) -> int:
        """Détecte le nombre total de pages"""
        pass

    @abstractmethod
    def parse_posts(self, soup: BeautifulSoup, topic_id: str) -> List[dict]:
        """Parse les posts d'une page"""
        pass

    def scrape_all_pages(
        self,
        base_url: str,
        topic_id: str,
        since_date: datetime,
        max_pages: int = 10,
        progress_callback: Optional[callable] = None
    ) -> Generator[dict, None, None]:
        """
        Scrape toutes les pages avec pagination.
        Yield les posts un par un pour feedback temps réel.
        """
        page = 1
        total_pages = None

        while page <= max_pages:
            url = self.get_page_url(base_url, page)

            try:
                response = self._make_request_with_retry(url, timeout=15)

                if response is None:
                    yield {"error": "Impossible de se connecter après plusieurs tentatives.", "page": page}
                    break

                if response.status_code == 403:
                    yield {
                        "error": "Accès refusé (403) après plusieurs tentatives. Protection anti-bot détectée.\n"
                                 "Solutions:\n"
                                 "1. Ajoutez des cookies Cloudflare (cf_clearance) dans les options avancées\n"
                                 "2. Utilisez l'extension 'Cookie-Editor' pour exporter les cookies du site\n"
                                 "3. Augmentez le délai entre les requêtes",
                        "page": page
                    }
                    break

                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'lxml')

                # Détecte le total de pages à la première itération
                if total_pages is None:
                    try:
                        detected_total = self.get_total_pages(soup)
                        total_pages = min(detected_total, max_pages) if detected_total > 0 else 1
                    except Exception as e:
                        logging.warning(f"Erreur detection pages: {e}")
                        total_pages = 1

                # Callback progression
                if progress_callback:
                    progress_callback(page, total_pages)

                # Parse les posts
                try:
                    posts = self.parse_posts(soup, topic_id)
                except Exception as e:
                    yield {"error": f"Erreur de parsing sur la page {page}: {str(e)}", "page": page}
                    posts = []

                stop_scraping = False
                for post in posts:
                    # 'date' is expected to be a datetime object here (parsed by the subclass)
                    post_date = post.get('date')

                    if post_date:
                        # Logic:
                        # If post_date >= since_date: keep it.
                        # If post_date < since_date: discard it AND stop scraping if threads are chronological.
                        # Usually threads are chronological (oldest first).
                        # So if we find a post OLDER than since_date, it means we are at the beginning of the thread (page 1).
                        # Wait, normal scraping goes Page 1 -> Page N.
                        # Page 1 has OLDEST posts. Page N has NEWEST posts.
                        # If user wants posts SINCE Jan 1st 2025:
                        # - We should probably check the LAST page first? Or filter as we go?
                        # Standard scraping: Start Page 1.
                        # Post 1 (2020) < 2025 -> Skip.
                        # ...
                        # Post X (2025) >= 2025 -> Keep.
                        #
                        # Optimization: If we know threads are chronological (Page 1 = Oldest),
                        # we iterate normally. We just skip posts until we hit the date.
                        # We do NOT stop scraping if date < since_date. We continue until we find newer posts.
                        #
                        # BUT, if the user only wants "Last 24h", we might want to start from the LAST page?
                        # The requirements say "Scrape messages with pagination management".
                        # Let's keep it simple: Start Page 1, scrape everything, filter by date.
                        # If max_pages is hit, we stop.

                        if post_date >= since_date:
                            yield post
                        else:
                            # Too old, but maybe subsequent posts are newer.
                            pass
                    else:
                        # No date found, yield anyway or log? Let's yield for manual check
                        yield post

                page += 1
                if page <= max_pages:
                    time.sleep(self.delay)

            except requests.RequestException as e:
                yield {"error": str(e), "page": page}
                break
