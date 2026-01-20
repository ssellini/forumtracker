# AGENTS.md

## Project Context
This is a Forum Tracker application built with Streamlit.
It scrapes forums (vBulletin, XenForo), translates posts from Spanish to French, and analyzes them using Google Gemini.

## Core Rules
1. **Language**: The UI must be entirely in **French**.
2. **Storage**: No database. Use `st.session_state` and JSON export/import.
3. **Scraping**: Use `requests` + `BeautifulSoup`. Handle pagination.
   - **Crucial**: Provide a way to inject manual Cookies/Headers in the UI to bypass Cloudflare (for sites like `spalumi.com`).
4. **Cloud Compatibility**: The app is designed for Streamlit Cloud.
5. **Data Models**: Use Dataclasses (`Post`, `Topic`) for structured data.

## Directory Structure
- `scrapers/`: Logic for vBulletin/XenForo parsing.
- `services/`: Logic for Translation, Analysis (Gemini), and Storage.
- `models/`: Data structures.
- `pages/`: Streamlit multipage files.
