from typing import List, Optional
from bs4 import BeautifulSoup
from scrapers.base import BaseScraper
from models.post import Post
import re
import logging

class XenForoScraper(BaseScraper):

    def get_page_url(self, base_url: str, page_num: int) -> str:
        """
        Construit l'URL XenForo.
        Ex: https://forum.com/threads/titre.123/ -> https://forum.com/threads/titre.123/page-2
        """
        if page_num == 1:
            return base_url

        # Check if already has page-X
        if 'page-' in base_url:
            return re.sub(r'page-\d+', f'page-{page_num}', base_url)

        # Add page-X at the end
        if base_url.endswith('/'):
            return f"{base_url}page-{page_num}"
        return f"{base_url}/page-{page_num}"

    def get_total_pages(self, soup: BeautifulSoup) -> int:
        """
        XenForo pagination structure:
        <ul class="pageNav-main"> ... <li class="pageNav-page"><a href="...">LastPage</a></li>
        """
        nav = soup.find('nav', class_='pageNavWrapper')
        if not nav:
            return 1

        # Try to find the last page number in the navigation list
        pages = nav.find_all('li', class_='pageNav-page')
        if pages:
            try:
                return int(pages[-1].get_text(strip=True))
            except ValueError:
                pass

        # Sometimes structure is simpler, just look for integers in pageNav
        links = nav.find_all('a')
        max_page = 1
        for link in links:
            txt = link.get_text(strip=True)
            if txt.isdigit():
                max_page = max(max_page, int(txt))
        return max_page

    def parse_posts(self, soup: BeautifulSoup, topic_id: str) -> List[dict]:
        posts_data = []

        # XenForo posts are usually in article.message
        articles = soup.find_all('article', class_='message')

        if not articles:
            # Fallback for some themes
            articles = soup.find_all('div', class_='message')

        for article in articles:
            try:
                # ID
                post_id = article.get('data-content', '')
                if not post_id and article.get('id'):
                    post_id = article.get('id')

                # Author
                author = article.get('data-author', 'Inconnu')
                if author == 'Inconnu':
                    author_elem = article.find('a', class_='username') or article.find('span', class_='username')
                    if author_elem:
                        author = author_elem.get_text(strip=True)

                # Date
                date_elem = article.find('time')
                date_str = ""
                date_val = None

                if date_elem:
                    # Prefer datetime attribute (ISO)
                    if date_elem.get('datetime'):
                        date_str = date_elem.get('datetime')
                    else:
                        date_str = date_elem.get_text(strip=True)
                else:
                    # Fallback to finding date in header
                    header = article.find('div', class_='message-attribution')
                    if header:
                        date_str = header.get_text(strip=True)

                date_obj = Post.parse_spanish_date(date_str)

                # Content
                content_div = article.find('div', class_='bbWrapper')
                if not content_div:
                    content_div = article.find('div', class_='message-body')

                content = ""
                if content_div:
                    # Remove quotes to avoid duplicating text
                    for quote in content_div.find_all('blockquote'):
                        quote.decompose()
                    content = content_div.get_text(separator='\n', strip=True)

                # Permalink
                permalink = None
                perma_elem = article.find('a', class_='u-concealed')
                if perma_elem and perma_elem.get('href'):
                    permalink = perma_elem.get('href')

                post = Post(
                    id=post_id or f"unknown-{len(posts_data)}",
                    topic_id=topic_id,
                    author=author,
                    date=date_obj,
                    content_original=content,
                    url=permalink
                )

                posts_data.append(post.to_dict())

            except Exception as e:
                logging.error(f"Error parsing post in XenForoScraper: {e}")
                continue

        return posts_data
