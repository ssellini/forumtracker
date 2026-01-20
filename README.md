# Forum Tracker

Agrégateur de Forums avec Traduction et Analyse IA (Streamlit).

## Fonctionnalités
- **Scraping** : Extraction de discussions depuis des forums XenForo et vBulletin.
- **Contournement Cloudflare** : Possibilité d'injecter manuellement des cookies pour les sites protégés (ex: `spalumi.com`).
- **Traduction** : Traduction automatique Espagnol -> Français via Google Translate.
- **Analyse IA** : Résumé, analyse de sentiment et extraction de points clés avec Google Gemini.
- **Export/Import** : Sauvegarde complète des sessions en JSON.

## Installation

1. Cloner le repo :
   ```bash
   git clone https://github.com/votre-user/forum-tracker.git
   cd forum-tracker
   ```

2. Installer les dépendances :
   ```bash
   pip install -r requirements.txt
   ```

3. (Optionnel) Configurer la clé API Gemini dans `.streamlit/secrets.toml` :
   ```toml
   GEMINI_API_KEY = "votre_clé_ici"
   ```

## Lancement

```bash
streamlit run app.py
```

## Utilisation

1. **Gestion Sources** : Ajoutez l'URL d'un sujet (Thread).
   - *Astuce* : Pour `spalumi.com`, utilisez une extension navigateur ("Cookie-Editor") pour copier vos cookies en JSON et collez-les dans les "Options Avancées" lors de l'ajout de la source.
2. **Extraction** : Choisissez la période et lancez le scraping.
3. **Traduction** : Traduisez les messages récupérés.
4. **Analyse IA** : Générez un rapport de synthèse.

## Structure du Projet
- `scrapers/` : Logique de scraping (Base, Detector, vBulletin, XenForo).
- `services/` : Services de traduction, stockage et IA.
- `models/` : Structures de données.
- `pages/` : Pages de l'interface Streamlit.
