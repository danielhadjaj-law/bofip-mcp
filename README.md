# BOFiP MCP — Doctrine fiscale française pour Claude

Serveur MCP donnant à Claude (ou tout autre client MCP) un accès structuré au **Bulletin Officiel des Finances Publiques – Impôts (BOFiP)**, la doctrine fiscale opposable de l'administration française.

> **À qui ça sert ?**
> Avocats fiscalistes, experts-comptables, juristes d'entreprise, chercheurs en droit fiscal — toute personne qui consulte régulièrement le BOFiP et travaille avec Claude.

## Pourquoi ce MCP ?

Le BOFiP est le corpus de référence de la doctrine fiscale française : commentaires administratifs, rescrits de portée générale, actualités doctrinales. Il est **opposable à l'administration sur le fondement des articles L. 80 A et L. 80 B du LPF**, ce qui en fait une source juridique de premier ordre.

Bien que la DGFiP mette le BOFiP à disposition en open data (Licence Ouverte 2.0), il n'existait jusqu'ici aucun serveur MCP permettant à Claude de l'interroger nativement. Ce projet comble ce manque.

## Les 13 outils exposés

| Outil | Usage |
|-------|-------|
| `rechercher_bofip` | Recherche plein texte standard |
| `rechercher_avancee_bofip` | Recherche multi-critères (série, division, type, dates) |
| `rechercher_rescrits` | Recherche limitée aux rescrits (L. 80 B LPF) |
| `rechercher_par_article_cgi` | BOI commentant un article du CGI / LPF / CDD |
| `rechercher_par_jurisprudence` | BOI citant une décision donnée |
| `get_boi` | Lecture complète d'un BOI |
| `get_paragraphe_boi` | Lecture ciblée d'un § précis |
| `explorer_bofip` | Navigation arborescente séries → divisions → BOI |
| `flux_bofip` | Veille doctrinale par semaine/période |
| `extraire_references_boi` | Cartographie des articles, jurisprudence et BOI cités |
| `get_url_historique_boi` | URL de consultation à une date passée |
| `lister_types_documents` | Types disponibles (Commentaire, Barème, Rescrit...) |
| `creer_ticket` | Feedback / bug / suggestion |

## Source de données

- **Dataset principal :** `bofip-vigueur` sur [data.economie.gouv.fr](https://data.economie.gouv.fr) (9 035 BOI, mise à jour hebdomadaire)
- **Dataset secondaire :** `bofip-impots` (flux hebdomadaires + stock mensuel pour les outils de veille)
- **Éditeur :** DGFiP (Direction Générale des Finances Publiques)
- **Licence :** Licence Ouverte v2.0 (Etalab)

## Installation et déploiement

Voir le fichier [`DEPLOIEMENT.md`](DEPLOIEMENT.md) pour le guide pas-à-pas (déploiement sur Render, gratuit, ~15 minutes).

## Architecture

```
bofip-mcp/
├── server.py              # Serveur MCP principal (13 tools)
├── bofip_client.py        # Client HTTP de l'API Opendatasoft
├── bofip_formatters.py    # Formatage des réponses pour LLM
├── requirements.txt       # Dépendances Python
├── render.yaml            # Configuration de déploiement Render
└── README.md              # Ce fichier
```

## Limites connues

- **Pas d'archive historique structurée.** L'open data DGFiP ne contient que la version en vigueur. Pour consulter une version passée d'un BOI, l'outil `get_url_historique_boi` génère l'URL officielle bofip.impots.gouv.fr.
- **Quotas anonymes.** L'API Opendatasoft applique un quota par IP. Pour un usage intensif, créer un compte gratuit sur data.economie.gouv.fr et fournir une clé API (variable d'environnement `ODS_API_KEY`, non implémentée par défaut).
- **Recherche par jurisprudence.** Repose sur une recherche plein texte ; les résultats peuvent être incomplets selon la formulation utilisée par l'administration dans ses commentaires.

## Auteur et licence

- **Code :** licence MIT
- **Données BOFiP :** Licence Ouverte 2.0 (DGFiP via Etalab)

Mainteneur : Daniel Hadjaj


