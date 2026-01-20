from abc import ABC, abstractmethod
from typing import List, Optional, Generator, Dict
from datetime import datetime
import time
import requests
from bs4 import BeautifulSoup
import logging

class BaseScraper(ABC):
    """Classe abstraite pour les scrapers de forums"""

    DEFAULT_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'es-ES,es;q=0.9,fr;q=0.8,en;q=0.7',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }

    def __init__(self, delay: float = 1.5, cookies: Optional[Dict] = None, user_agent: Optional[str] = None):
        self.delay = delay
        self.session = requests.Session()

        # Update headers
        headers = self.DEFAULT_HEADERS.copy()
        if user_agent:
            headers['User-Agent'] = user_agent
        self.session.headers.update(headers)

        # Set cookies if provided
        if cookies:
            self.session.cookies.update(cookies)

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
                response = self.session.get(url, timeout=15)
                if response.status_code == 403:
                    yield {"error": "Accès refusé (403). Protection Cloudflare probable. Essayez d'ajouter des cookies manuellement.", "page": page}
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
