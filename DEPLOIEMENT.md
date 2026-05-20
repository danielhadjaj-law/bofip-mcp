# Guide de déploiement — BOFiP MCP sur Render

Ce guide vous emmène de zéro jusqu'à un serveur MCP fonctionnel utilisable dans Claude, en ~15 minutes. **Aucune compétence technique préalable n'est requise.**

---

## Vue d'ensemble

```
[Votre ordinateur]
    └→ téléchargez les fichiers du projet
        └→ déposez-les sur GitHub (stockage en ligne)
            └→ Render lit GitHub et fait tourner le serveur
                └→ vous connectez Claude au serveur via une URL
```

**Temps estimé :** 15 minutes (la première fois). Ensuite, les mises à jour prennent 2 minutes.

**Coût :** 0 € (free tier Render + GitHub).

---

## ÉTAPE 1 — Créer un compte GitHub (3 min)

GitHub est le service où sera stocké le code. C'est gratuit.

1. Allez sur **[github.com](https://github.com)**
2. Cliquez sur **"Sign up"** (en haut à droite)
3. Renseignez :
   - une adresse email (idéalement pro pour ce projet)
   - un mot de passe
   - un nom d'utilisateur (ex: `dan-cosich` ou `dan-fiscaliste`) — il apparaîtra publiquement
4. Validez via l'email reçu
5. Choisissez le plan **"Free"** quand on vous le propose

✅ Vous avez maintenant un compte GitHub.

---

## ÉTAPE 2 — Créer un dépôt et uploader les fichiers (3 min)

Un "dépôt" (*repository*, ou *repo* en raccourci) est simplement un dossier de fichiers stocké sur GitHub.

1. Une fois connecté, cliquez sur le **"+"** en haut à droite → **"New repository"**
2. Configurez :
   - **Repository name** : `bofip-mcp`
   - **Description** : `Serveur MCP pour le BOFiP-Impôts français`
   - **Public** (recommandé pour visibilité du projet) ou Private (privé)
   - Ne cochez **rien** ("Add a README", etc.) — on va déposer les fichiers nous-mêmes
3. Cliquez **"Create repository"**

Vous arrivez sur une page vide avec des instructions techniques. **Ignorez-les.** Cherchez le petit lien **"uploading an existing file"** (en bas de la liste d'instructions).

4. Cliquez sur **"uploading an existing file"**
5. Glissez-déposez **TOUS les fichiers** du dossier `bofip-mcp/` que je vous ai fourni :
   - `server.py`
   - `bofip_client.py`
   - `bofip_formatters.py`
   - `requirements.txt`
   - `render.yaml`
   - `README.md`
   - `DEPLOIEMENT.md` (ce fichier)
   - `.gitignore`
6. Dans la zone "Commit changes" en bas, laissez le message par défaut ("Add files via upload") et cliquez **"Commit changes"**

✅ Les fichiers sont maintenant sur GitHub.

---

## ÉTAPE 3 — Créer un compte Render (2 min)

Render est l'hébergeur où le serveur tournera.

1. Allez sur **[render.com](https://render.com)**
2. Cliquez sur **"Get Started"**
3. Choisissez **"Sign up with GitHub"** (le plus simple — réutilise le compte créé à l'étape 1)
4. Autorisez Render à voir vos dépôts GitHub

✅ Compte Render créé et lié à GitHub.

---

## ÉTAPE 4 — Déployer le serveur sur Render (3 min)

1. Sur le tableau de bord Render, cliquez sur **"New +"** → **"Web Service"**
2. Sélectionnez le dépôt `bofip-mcp` que vous venez de créer
   - Si vous ne le voyez pas, cliquez sur "Configure account" et donnez à Render l'accès au dépôt
3. Render détecte automatiquement le fichier `render.yaml` et pré-remplit la configuration. Vérifiez :
   - **Name** : `bofip-mcp` (ou autre, c'est juste un libellé)
   - **Region** : Frankfurt (proche de la France, plus rapide)
   - **Branch** : `main`
   - **Runtime** : Python
   - **Build Command** : `pip install -r requirements.txt`
   - **Start Command** : `python server.py`
   - **Instance Type** : `Free`
4. Cliquez **"Create Web Service"** en bas

Render commence le déploiement. Vous voyez des logs défiler. C'est normal — le serveur :
- télécharge les dépendances (FastMCP, httpx) → ~30 secondes
- démarre le serveur → ~5 secondes

Quand vous voyez `Your service is live 🎉` ou un message similaire, c'est prêt.

5. **Notez l'URL publique** affichée en haut de la page Render. Elle ressemble à :
   ```
   https://bofip-mcp-xxxx.onrender.com
   ```

✅ Le serveur tourne.

---

## ÉTAPE 5 — Connecter le serveur à Claude (2 min)

1. Allez sur **[claude.ai](https://claude.ai)**
2. Cliquez sur votre photo de profil → **"Paramètres"** → **"Connecteurs"** (ou "Connectors")
3. Cliquez **"Ajouter un connecteur personnalisé"** (ou "Add custom connector")
4. Renseignez :
   - **Nom** : `BOFiP-Impôts`
   - **URL** : `https://bofip-mcp-xxxx.onrender.com/mcp` (l'URL Render + `/mcp` à la fin)
   - Pas d'authentification requise
5. Validez

Claude se connecte au serveur et liste les 13 outils disponibles.

✅ **C'est terminé.** Dans n'importe quelle conversation Claude future, je verrai et utiliserai ces 13 outils automatiquement quand pertinent.

---

## Tester le bon fonctionnement

Ouvrez une nouvelle conversation Claude et essayez :

> *"Cherche dans le BOFiP les commentaires sur la vérification de comptabilité."*

Claude doit appeler `rechercher_bofip("vérification de comptabilité")` et vous restituer les résultats.

Autre test plus avancé :

> *"Récupère le BOI-CF-IOR-10 complet."*

→ appelle `get_boi("BOI-CF-IOR-10")`.

Ou encore :

> *"Liste les séries du BOFiP avec leur volume."*

→ appelle `explorer_bofip()`.

---

## Maintenance et mises à jour

**Si vous voulez modifier le serveur** (ajouter un outil, corriger un bug, etc.) :
1. Modifiez les fichiers sur votre ordinateur
2. Allez sur GitHub, dans votre dépôt `bofip-mcp`
3. Pour chaque fichier modifié : cliquez sur le fichier → icône crayon → collez le nouveau contenu → "Commit changes"
4. Render détecte automatiquement le changement et redéploie en 1-2 minutes.

---

## En cas de problème

### Le service Render dort et met du temps à se réveiller

C'est normal sur le free tier : après 15 min d'inactivité, le service se met en veille. Le prochain appel le réveille en ~30 secondes. Pour éviter ça :
- Soit acceptez les 30 secondes (négligeable pour un usage personnel)
- Soit passez au plan payant ($7/mois pour le "Starter")
- Soit configurez un ping automatique (UptimeRobot, gratuit, 5 min)

### Claude ne voit pas les outils

- Vérifiez que l'URL se termine bien par `/mcp` dans la config du connecteur
- Vérifiez sur Render que le service est bien "Live" (vert)
- Ouvrez l'URL `https://votre-url.onrender.com/mcp` dans un navigateur — vous devriez voir une réponse (même si elle est cryptique, ce n'est pas une erreur 500)

### Une recherche ne retourne rien

- L'API DGFiP a un quota anonyme par IP. Si vous l'avez beaucoup sollicitée, attendez 1h.
- Pour un usage intensif, créez un compte sur data.economie.gouv.fr, récupérez une clé API, et ajoutez-la aux variables d'environnement Render.

### Le service Render s'arrête après plusieurs jours

Le free tier Render fait tourner les services dans un quota de 750h/mois (suffisant pour un service unique). Vérifiez sur le dashboard.

---

## Soumettre au registre public Anthropic (optionnel)

Une fois le serveur fonctionnel et testé, vous pouvez le proposer au registre Anthropic pour qu'il soit visible par tous les utilisateurs Claude. La procédure est documentée sur le site [Anthropic MCP Connectors](https://www.anthropic.com/news/connectors).

**Avant de soumettre :**
- Vérifiez que le serveur tourne de manière stable
- Ajoutez votre nom et coordonnées dans le README
- Créez un logo simple (favicon) pour le dépôt
- Préparez un texte de description en anglais (le registre est international)

C'est là que votre positionnement public commence vraiment.
