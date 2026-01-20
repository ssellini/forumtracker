# Déploiement sur Streamlit Cloud (Interface Web)

Ce guide explique comment déployer l'application **Forum Tracker** gratuitement sur Streamlit Community Cloud en utilisant l'interface graphique.

## Pré-requis

1. Avoir un compte [GitHub](https://github.com/).
2. Avoir un compte [Streamlit Cloud](https://share.streamlit.io/).
3. Avoir "Poussé" (Push) ce projet sur un dépôt GitHub (Public ou Privé).

---

## Étape 1 : Connexion à Streamlit Cloud

1. Allez sur [share.streamlit.io](https://share.streamlit.io/).
2. Cliquez sur le bouton bleu **"New app"** (Nouvelle application) en haut à droite.
3. Si ce n'est pas déjà fait, autorisez Streamlit à accéder à vos dépôts GitHub.

## Étape 2 : Configuration du déploiement

Dans l'écran "Deploy an app", remplissez le formulaire :

1. **Repository** : Cliquez sur le champ et sélectionnez le dépôt GitHub contenant votre code (ex: `votre-pseudo/forum-tracker`).
2. **Branch** : Laissez généralement `main` ou `master` (ou la branche où vous avez mis votre code).
3. **Main file path** : Sélectionnez ou écrivez `app.py`.
4. **App URL** (Optionnel) : Vous pouvez choisir un sous-domaine personnalisé si disponible.

## Étape 3 : Configuration des Secrets (Clé API)

**Important** : Ne sautez pas cette étape si vous voulez utiliser l'analyse IA sans entrer la clé à chaque fois.

1. Cliquez sur **"Advanced settings..."** (Paramètres avancés) en bas du formulaire.
2. Une fenêtre modale s'ouvre. Allez dans l'onglet **"Secrets"**.
3. Dans la zone de texte, copiez le contenu suivant en remplaçant par votre vraie clé API Google Gemini :

```toml
GEMINI_API_KEY = "AIzaSyD......votre_cle_ici......"
```

4. Cliquez sur **"Save"**.

## Étape 4 : Lancement

1. Cliquez sur le bouton **"Deploy!"**.
2. Streamlit va commencer à "cuisiner" votre application :
   - Il télécharge le code.
   - Il installe les dépendances listées dans `requirements.txt`.
   - Il lance `app.py`.

Cela prend généralement 1 à 3 minutes. Vous verrez une console noire à droite montrant la progression.

## Étape 5 : Vérification

Une fois terminé, votre application s'ouvrira automatiquement.
Vous verrez l'interface "Forum Tracker".

### Dépannage courant :
- **Erreur "ModuleNotFoundError"** : Vérifiez que le fichier `requirements.txt` est bien à la racine du dépôt.
- **Erreur 403 lors du scraping** : C'est normal pour certains sites protégés (Cloudflare). Utilisez l'option "Options Avancées" dans la page "Gestion Sources" pour coller vos cookies manuellement.
