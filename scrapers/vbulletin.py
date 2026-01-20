from typing import List
from bs4 import BeautifulSoup
from scrapers.base import BaseScraper
from models.post import Post
import re
import logging

class VBulletinScraper(BaseScraper):

    def get_page_url(self, base_url: str, page_num: int) -> str:
        """
        Construit l'URL vBulletin.
        Patterns:
        1. showthread.php?t=123 -> showthread.php?t=123&page=2
        2. /threads/title.123/ -> /threads/title.123/page2
        """
        if page_num == 1:
            return base_url

        if '?' in base_url:
            # Type Query param (e.g. showthread.php?t=...)
            if 'page=' in base_url:
                return re.sub(r'page=\d+', f'page={page_num}', base_url)
            return f"{base_url}&page={page_num}"
        else:
            # Type Rewrite URL
            if base_url.endswith('/'):
                return f"{base_url}page{page_num}"
            return f"{base_url}/page{page_num}"

    def get_total_pages(self, soup: BeautifulSoup) -> int:
        # Generic vBulletin pagination check

        # Look for "Page X of Y" text
        nav_text = soup.find(string=re.compile(r'Page \d+ of \d+'))
        if nav_text:
            match = re.search(r'of (\d+)', nav_text)
            if match:
                return int(match.group(1))

        # Look for pagination links
        pagenav = soup.find('div', class_='pagenav') or soup.find('div', class_='pagination')
        if pagenav:
            links = pagenav.find_all('a')
            max_page = 1
            for link in links:
                # vBulletin often has 'Last Page' link with title="Last Page"
                if 'Last' in link.get('title', '') or 'Última' in link.get('title', ''):
                    href = link.get('href')
                    match = re.search(r'page=(\d+)', href) or re.search(r'page(\d+)', href)
                    if match:
                        return int(match.group(1))

                txt = link.get_text(strip=True)
                if txt.isdigit():
                    max_page = max(max_page, int(txt))
            return max_page

        return 1

    def parse_posts(self, soup: BeautifulSoup, topic_id: str) -> List[dict]:
        posts_data = []

        # vBulletin has multiple layouts.
        # Strategy: Find container that looks like a post.

        # Pattern 1: vBulletin 3/4 legacy (Tables or LIs)
        # Selectors: div.postbit, li.postbit, li.postbitlegacy, table.tborder (checking id starts with post)

        candidates = []
        candidates.extend(soup.find_all('li', class_='postbit'))
        candidates.extend(soup.find_all('li', class_='postbitlegacy'))
        candidates.extend(soup.find_all('div', class_='postbit'))

        if not candidates:
            # Fallback for vB 3.x tables
            # Find divs with id starting with 'post_message_' and work backwards
            msgs = soup.find_all('div', id=re.compile(r'^post_message_\d+'))
            for msg in msgs:
                # This is just content, we need to wrap it to simulate a post object
                # Or traverse up to find the container
                candidates.append(msg.find_parent('table'))

        for item in candidates:
            if not item: continue

            try:
                # ID
                post_id = None
                # Try to find id in anchor
                anchor = item.find('a', id=re.compile(r'^post\d+'))
                if anchor:
                    post_id = anchor.get('id')
                else:
                    # Try to extract from edit link or reply link
                    link = item.find('a', href=re.compile(r'p=\d+'))
                    if link:
                        m = re.search(r'p=(\d+)', link['href'])
                        if m: post_id = m.group(1)

                # Author
                author = "Inconnu"
                author_elem = item.find('a', class_='username') or item.find('a', class_='bigusername')
                if author_elem:
                    author = author_elem.get_text(strip=True)

                # Date
                date_str = ""
                # Usually in a thead or a div near top
                # vB4: <span class="date">...</span>
                date_elem = item.find('span', class_='date')
                if not date_elem:
                    # vB3: inside first td of table usually "Yesterday, 10:00 PM"
                    # Hard to pinpoint, try searching text node with date pattern?
                    # Or look for class="time"
                    date_elem = item.find('span', class_='time')

                if date_elem:
                     date_str = date_elem.get_parent().get_text(strip=True) # Get date + time
                else:
                    # Fallback text search at top of post
                    text_nodes = item.stripped_strings
                    for s in text_nodes:
                        # Simple heuristic: if it contains a year or "Ayer/Hoy"
                        if any(x in s.lower() for x in ['ayer', 'hoy', '202']):
                            date_str = s
                            break

                date_obj = Post.parse_spanish_date(date_str)

                # Content
                content = ""
                # vB4
                msg_div = item.find('div', class_='content')
                if not msg_div:
                    # vB3
                    msg_div = item.find('div', id=re.compile(r'post_message_'))

                if msg_div:
                    # Remove quotes
                    for quote in msg_div.find_all('div', class_='quote'):
                        quote.decompose()
                    content = msg_div.get_text(separator='\n', strip=True)

                # Permalink
                permalink = None
                perma_elem = item.find('a', class_='postcounter')
                if perma_elem:
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
                logging.error(f"Error parsing post in VBulletinScraper: {e}")
                continue

        return posts_data
