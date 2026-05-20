# Soumission au registre Anthropic — brouillon

Document préparatoire pour la soumission du serveur MCP au registre public Anthropic, une fois le déploiement validé en production.

## Métadonnées de soumission

**Name :** BOFiP-Impôts
*Alternative en anglais : "French Tax Doctrine (BOFiP)"*

**Tagline (en anglais) :**
> Access the official French tax doctrine (BOFiP-Impôts) — searchable commentaries, rescripts and case law citations from the French tax administration.

**Tagline (en français) :**
> Accédez à la doctrine fiscale française (BOFiP-Impôts) : commentaires administratifs, rescrits, références jurisprudentielles, en temps réel depuis l'open data DGFiP.

**Description longue (en anglais) :**

Provides Claude with native access to the **Bulletin Officiel des Finances Publiques – Impôts (BOFiP)**, the consolidated body of French tax administrative doctrine published by the DGFiP (French Tax Administration).

This MCP server exposes 13 specialized tools designed for legal and tax professionals:

- **Search** — full-text, multi-criteria, by article (CGI/LPF/CDD), by case law citation, or filtered to rescripts only
- **Read** — full BOI documents or specific numbered paragraphs (e.g. BOI-CF-IOR-10, § 250)
- **Explore** — hierarchical navigation through tax series (CF, IR, IS, VAT…) and divisions
- **Analyze** — extraction of cited articles, case law and cross-referenced BOI
- **Monitor** — weekly publication feeds and document type listings
- **Historical** — URL generation for consulting historical versions of any BOI

**Data source:** DGFiP open data, updated weekly, under the French Open License v2.0 (Etalab). 9,000+ doctrinal documents covering all major taxes (income tax, corporate tax, VAT, registration duties, tax procedure, litigation, etc.).

**Designed for:** tax lawyers, certified accountants, corporate counsel, tax litigation professionals, and academic researchers in French tax law.

**Keywords:** french tax law, fiscal law, BOFiP, DGFiP, tax doctrine, tax administration, droit fiscal, doctrine fiscale, fiscalité française

**Catégorie suggérée :** Legal & Compliance / Government Data

## Liens à fournir

- **Repository URL** : `https://github.com/[votre-username]/bofip-mcp`
- **MCP endpoint URL** : `https://bofip-mcp-xxxx.onrender.com/mcp` (URL Render après déploiement)
- **Documentation URL** : pointer vers le README du dépôt
- **Author URL** : votre LinkedIn / site cabinet
- **License** : MIT (code) + Licence Ouverte 2.0 (données)

## Icône / logo

Suggestions de design simple :
- Variante 1 : carrés bleu marine "BOFiP" en typographie sans-serif (rappel administratif français)
- Variante 2 : superposition stylisée d'un Code juridique + d'un sigle "F" (français)
- Variante 3 : silhouette Marianne stylisée + texte "BOFiP" en bas

Format requis par Anthropic : PNG ou SVG, carré, 256×256 minimum. À produire avant soumission.

## Exemples d'usage à fournir

À inclure dans la fiche du registre — montre la valeur immédiate :

**Exemple 1 — recherche thématique :**
> *"Quels sont les BOI commentant l'article L. 80 A du LPF ?"*
> → `rechercher_par_article_cgi("L. 80 A", code="LPF")`

**Exemple 2 — lecture précise :**
> *"Donne-moi le § 250 du BOI-CF-IOR-10."*
> → `get_paragraphe_boi("BOI-CF-IOR-10", 250)`

**Exemple 3 — analyse :**
> *"Quelles décisions du Conseil d'État sont citées dans le BOI-IR-BASE-10 ?"*
> → `extraire_references_boi("BOI-IR-BASE-10")`

**Exemple 4 — veille :**
> *"Qu'est-ce qui a été publié au BOFiP la semaine dernière ?"*
> → `flux_bofip(date_debut="...", date_fin="...")`

## Authentification

**Type :** Aucune (`is_authless: true`)

Le serveur ne nécessite aucune clé d'API utilisateur. Les appels à l'open data DGFiP sont anonymes (quota par IP du serveur). Aucune donnée personnelle n'est collectée ni transmise.

## Considérations de conformité

- **Données :** publiques, sous Licence Ouverte 2.0 Etalab. Aucun traitement de données à caractère personnel.
- **Source officielle :** données issues directement de l'API publique du Ministère de l'Économie (data.economie.gouv.fr), opérée par la DGFiP.
- **Pas de retraitement éditorial :** le serveur retourne les contenus tels que publiés par l'administration, avec leurs permaliens officiels.

## Texte d'introduction pour les utilisateurs

À afficher lors de la première connexion au connecteur dans Claude :

> Le connecteur BOFiP-Impôts vous donne accès à la doctrine fiscale française officielle, telle que publiée et mise à jour hebdomadairement par la DGFiP. Toutes les recherches et lectures de BOI s'effectuent en temps réel sur l'open data du Ministère de l'Économie, sous Licence Ouverte 2.0. Pour les contentieux fiscaux et le conseil juridique, vérifiez toujours la version la plus récente sur bofip.impots.gouv.fr et tenez compte de la date d'opposabilité de la doctrine au regard de votre cas d'espèce.

## Procédure de soumission (à confirmer auprès d'Anthropic)

À la date de rédaction (mai 2026), Anthropic propose la soumission au registre MCP via :
1. Le formulaire sur [anthropic.com/mcp/submit](https://anthropic.com/mcp/submit) *(URL à vérifier)*
2. Ou par contact direct dev-rel@anthropic.com avec lien vers le repo et l'endpoint MCP

**Délai d'examen typique :** 1 à 4 semaines selon le volume de soumissions.

**Critères d'acceptation usuels :**
- Serveur stable (uptime >95%)
- Documentation claire (README + exemples)
- Pas de tools dangereux ou trompeurs
- Pas de retraitement biaisé des données source
- Conformité aux conditions d'utilisation Anthropic

## Avant de soumettre — checklist

- [ ] Serveur déployé sur Render et fonctionnel depuis au moins 7 jours sans incident
- [ ] Tests manuels passés sur les 13 outils dans une vraie conversation Claude
- [ ] README finalisé avec votre nom et contact
- [ ] DEPLOIEMENT.md complet
- [ ] LICENSE (MIT) ajouté au dépôt
- [ ] Logo/icône produit
- [ ] Page de contact / mentions légales mise en place (sur votre site ou en lien)
- [ ] 2-3 exemples d'usage testés et présentables
