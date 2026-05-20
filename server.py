"""
Serveur MCP BOFiP — Doctrine fiscale française

Expose 13 outils permettant d'interroger le Bulletin Officiel des Finances
Publiques (BOFiP-Impôts) via l'API Opendatasoft de data.economie.gouv.fr.

Source de données : DGFiP, Licence Ouverte v2.0 (Etalab).

Author: [VOTRE NOM]
License: MIT (pour le code) / Licence Ouverte 2.0 (pour les données)
"""

import os
from typing import Optional
from datetime import datetime
from fastmcp import FastMCP

from bofip_client import (
    search_vigueur,
    search_flux,
    facets_vigueur,
    build_search_clause,
    validate_boi_id,
    escape_ods_string,
    BofipAPIError,
)
from bofip_formatters import (
    format_search_results,
    format_boi_full,
    format_facet_results,
    format_flux_results,
    extract_paragraphe,
    list_paragraphes_numbers,
)

# Initialisation du serveur MCP
mcp = FastMCP(
    name="bofip-impots",
    instructions=(
        "Serveur MCP donnant accès à la doctrine fiscale française (BOFiP-Impôts) "
        "via l'API publique de la DGFiP. Permet de rechercher, lire et analyser "
        "les commentaires administratifs en vigueur, les rescrits de portée "
        "générale et les actualités doctrinales. Données sous Licence Ouverte 2.0."
    ),
)


# ═══════════════════════════════════════════════════════════════════════
# OUTIL 1 — Recherche plein texte basique
# ═══════════════════════════════════════════════════════════════════════

@mcp.tool()
async def rechercher_bofip(
    query: str,
    page: int = 1,
    page_size: int = 10,
) -> str:
    """
    Recherche plein texte dans le BOFiP en vigueur.

    Args:
        query: Termes de recherche (mots-clés ou expression).
            Exemples : "vérification de comptabilité", "abus de droit fiscal",
            "régime mère-fille", "provision pour créances douteuses".
        page: Numéro de page (défaut 1, ≥1).
        page_size: Nombre de résultats par page (défaut 10, max 100).

    Returns:
        Liste paginée de BOI correspondants, avec identifiant juridique,
        titre, série, division, type et extrait. Le contenu intégral n'est
        pas inclus — utiliser get_boi() pour le lire en entier.

    Exemples:
        - rechercher_bofip("vérification de comptabilité")
        - rechercher_bofip("régime mère fille", page=2)
    """
    if page < 1:
        return "❌ Erreur : 'page' doit être ≥ 1."
    page_size = max(1, min(page_size, 100))

    try:
        response = await search_vigueur(
            where=build_search_clause(query),
            select="identifiant_juridique,titre,serie,division,type,debut_de_validite,permalien,contenu",
            limit=page_size,
            offset=(page - 1) * page_size,
            order_by="debut_de_validite DESC",
        )
        return format_search_results(
            response, page, page_size, "rechercher_bofip", include_extrait=True
        )
    except BofipAPIError as e:
        return f"❌ {e}"


# ═══════════════════════════════════════════════════════════════════════
# OUTIL 2 — Recherche avancée multi-critères
# ═══════════════════════════════════════════════════════════════════════

@mcp.tool()
async def rechercher_avancee_bofip(
    query: Optional[str] = None,
    serie: Optional[str] = None,
    division: Optional[str] = None,
    type_document: Optional[str] = None,
    date_min: Optional[str] = None,
    date_max: Optional[str] = None,
    page: int = 1,
    page_size: int = 10,
) -> str:
    """
    Recherche multi-critères dans le BOFiP en vigueur.

    Combine plusieurs filtres : texte, série, division, type de document
    et plage de dates de validité.

    Args:
        query: Termes de recherche (optionnel).
        serie: Série BOFiP (ex: "CF", "IR", "IS", "TVA", "CTX", "ENR", "RPPM",
            "BIC", "BNC", "BA", "IF", "RES", "TPS", "DJC", "INT", "REC", "SJ").
        division: Division au sein de la série (ex: "IOR", "PGR", "INF", "DECLA").
        type_document: Type de document ("Contenu", "Actualité", "Rescrit"...).
        date_min: Date de début de validité minimale (format YYYY-MM-DD).
        date_max: Date de début de validité maximale (format YYYY-MM-DD).
        page: Numéro de page (défaut 1).
        page_size: Nombre de résultats par page (défaut 10, max 100).

    Returns:
        Liste paginée des BOI correspondant à tous les critères.

    Exemples:
        - rechercher_avancee_bofip(query="vérification", serie="CF")
        - rechercher_avancee_bofip(serie="IR", date_min="2024-01-01")
        - rechercher_avancee_bofip(query="abus de droit", serie="CF", division="IOR")
    """
    if page < 1:
        return "❌ Erreur : 'page' doit être ≥ 1."
    page_size = max(1, min(page_size, 100))

    clauses = []
    refine = []

    if query:
        clauses.append(build_search_clause(query))
    if serie:
        refine.append(f"serie:{serie.upper()}")
    if division:
        refine.append(f"division:{division.upper()}")
    if type_document:
        refine.append(f"type:{type_document}")
    if date_min:
        try:
            datetime.strptime(date_min, "%Y-%m-%d")
            clauses.append(f"debut_de_validite >= date'{date_min}'")
        except ValueError:
            return f"❌ Erreur : 'date_min' doit être au format YYYY-MM-DD (reçu : {date_min})."
    if date_max:
        try:
            datetime.strptime(date_max, "%Y-%m-%d")
            clauses.append(f"debut_de_validite <= date'{date_max}'")
        except ValueError:
            return f"❌ Erreur : 'date_max' doit être au format YYYY-MM-DD (reçu : {date_max})."

    if not clauses and not refine:
        return (
            "❌ Erreur : au moins un critère est requis (query, serie, division, "
            "type_document, date_min ou date_max)."
        )

    where = " AND ".join(clauses) if clauses else None

    try:
        response = await search_vigueur(
            where=where,
            refine=refine if refine else None,
            select="identifiant_juridique,titre,serie,division,type,debut_de_validite,permalien,contenu",
            limit=page_size,
            offset=(page - 1) * page_size,
            order_by="debut_de_validite DESC",
        )
        return format_search_results(
            response, page, page_size, "rechercher_avancee_bofip", include_extrait=True
        )
    except BofipAPIError as e:
        return f"❌ {e}"


# ═══════════════════════════════════════════════════════════════════════
# OUTIL 3 — Recherche dans les rescrits
# ═══════════════════════════════════════════════════════════════════════

@mcp.tool()
async def rechercher_rescrits(
    query: Optional[str] = None,
    page: int = 1,
    page_size: int = 10,
) -> str:
    """
    Recherche dans les rescrits de portée générale publiés au BOFiP.

    Les rescrits sont des prises de position formelles de l'administration
    fiscale, opposables sur le fondement de l'article L. 80 B du LPF. Leur
    statut juridique est distinct des commentaires généraux : ils peuvent
    être invoqués par les contribuables placés dans une situation identique.

    Args:
        query: Termes de recherche (optionnel). Sans query, retourne les
            rescrits les plus récents.
        page: Numéro de page (défaut 1).
        page_size: Nombre de résultats par page (défaut 10, max 100).

    Returns:
        Liste paginée des rescrits correspondants, du plus récent au plus ancien.

    Note:
        Le filtrage est effectué sur le champ "titre" qui mentionne "Rescrit"
        ou via le champ "type" si disponible. Pour les recherches très précises,
        utilisez rechercher_avancee_bofip() avec query incluant "rescrit".
    """
    if page < 1:
        return "❌ Erreur : 'page' doit être ≥ 1."
    page_size = max(1, min(page_size, 100))

    # Les rescrits BOFiP ont "RES -" ou "Rescrit" dans le titre, ou la série "RES"
    # On combine plusieurs critères pour maximiser le rappel
    base_clause = '(search(titre, "rescrit") OR serie="RES")'
    clauses = [base_clause]

    if query:
        clauses.append(build_search_clause(query))

    where = " AND ".join(clauses)

    try:
        response = await search_vigueur(
            where=where,
            select="identifiant_juridique,titre,serie,division,type,debut_de_validite,permalien,contenu",
            limit=page_size,
            offset=(page - 1) * page_size,
            order_by="debut_de_validite DESC",
        )
        return format_search_results(
            response, page, page_size, "rechercher_rescrits", include_extrait=True
        )
    except BofipAPIError as e:
        return f"❌ {e}"


# ═══════════════════════════════════════════════════════════════════════
# OUTIL 4 — Recherche par article CGI/LPF
# ═══════════════════════════════════════════════════════════════════════

@mcp.tool()
async def rechercher_par_article_cgi(
    article: str,
    code: str = "CGI",
    page: int = 1,
    page_size: int = 10,
) -> str:
    """
    Recherche les BOI commentant un article précis du CGI, du LPF ou du CDD.

    Args:
        article: Numéro ou désignation de l'article. Exemples :
            - "209" (article 209 CGI - report en avant des déficits)
            - "L. 80 A" (LPF - opposabilité de la doctrine)
            - "1729" (CGI - majorations pour manquement)
            - "39" (CGI - charges déductibles)
            - "885 E" (CGI - assiette ISF, abrogé)
        code: Code visé : "CGI" (défaut), "LPF" (Livre des procédures fiscales),
            "CDD" (Code des douanes).
        page: Numéro de page (défaut 1).
        page_size: Nombre de résultats (défaut 10, max 100).

    Returns:
        Liste paginée des BOI mentionnant cet article.

    Exemples:
        - rechercher_par_article_cgi("209")
        - rechercher_par_article_cgi("L. 80 A", code="LPF")
        - rechercher_par_article_cgi("1729", code="CGI")
    """
    if page < 1:
        return "❌ Erreur : 'page' doit être ≥ 1."
    page_size = max(1, min(page_size, 100))

    code_upper = code.upper()
    if code_upper not in ("CGI", "LPF", "CDD"):
        return f"❌ Erreur : code doit être CGI, LPF ou CDD (reçu : {code})."

    # Recherche plusieurs formulations possibles dans le contenu
    article_clean = article.strip()
    # Formulations courantes : "article 209 du CGI", "art. 209 du CGI", "209 du CGI"
    query = f"article {article_clean} {code_upper}"

    try:
        response = await search_vigueur(
            where=build_search_clause(query),
            select="identifiant_juridique,titre,serie,division,type,debut_de_validite,permalien,contenu",
            limit=page_size,
            offset=(page - 1) * page_size,
            order_by="debut_de_validite DESC",
        )
        return format_search_results(
            response, page, page_size, "rechercher_par_article_cgi", include_extrait=True
        )
    except BofipAPIError as e:
        return f"❌ {e}"


# ═══════════════════════════════════════════════════════════════════════
# OUTIL 5 — Recherche par jurisprudence
# ═══════════════════════════════════════════════════════════════════════

@mcp.tool()
async def rechercher_par_jurisprudence(
    reference: str,
    page: int = 1,
    page_size: int = 10,
) -> str:
    """
    Recherche les BOI citant une décision de jurisprudence.

    Très utile en contentieux : permet de savoir si l'administration a
    intégré (ou non) une décision dans sa doctrine. Si oui, la décision
    est opposable au sens de l'article L. 80 A du LPF. Si non, c'est un
    argument de divergence à exploiter.

    Args:
        reference: Référence de la décision. Formes acceptées :
            - "CE 8 mars 2023 463267"
            - "CE 463267"
            - "Conseil d'État 8 mars 2023"
            - "Cass. com. 25 juin 2019 17-31657"
            - Le numéro de pourvoi/requête seul fonctionne souvent.
        page: Numéro de page (défaut 1).
        page_size: Nombre de résultats (défaut 10, max 100).

    Returns:
        Liste paginée des BOI citant cette décision.

    Exemples:
        - rechercher_par_jurisprudence("CE 463267")
        - rechercher_par_jurisprudence("CE 8 mars 2023 SNE Martelli")
        - rechercher_par_jurisprudence("Cass. com. 17-31657")
    """
    if page < 1:
        return "❌ Erreur : 'page' doit être ≥ 1."
    page_size = max(1, min(page_size, 100))

    try:
        response = await search_vigueur(
            where=build_search_clause(reference),
            select="identifiant_juridique,titre,serie,division,type,debut_de_validite,permalien,contenu",
            limit=page_size,
            offset=(page - 1) * page_size,
            order_by="debut_de_validite DESC",
        )
        return format_search_results(
            response, page, page_size, "rechercher_par_jurisprudence", include_extrait=True
        )
    except BofipAPIError as e:
        return f"❌ {e}"


# ═══════════════════════════════════════════════════════════════════════
# OUTIL 6 — Lecture complète d'un BOI
# ═══════════════════════════════════════════════════════════════════════

@mcp.tool()
async def get_boi(
    identifiant_juridique: str,
    format: str = "text",
) -> str:
    """
    Récupère le contenu intégral d'un BOI par son identifiant juridique.

    Args:
        identifiant_juridique: Identifiant du BOI au format BOI-XX-YY[-ZZ...].
            Exemples : "BOI-CF-IOR-10", "BOI-IR-BASE-10-20-30",
            "BOI-TVA-DECLA-20-30-20-30".
        format: "text" pour le texte brut (défaut), "html" pour la structure HTML.

    Returns:
        Contenu intégral du BOI avec métadonnées (titre, série, division,
        date de validité, permalien officiel) et le texte doctrinal.

    Note:
        Pour ne récupérer qu'un § précis et économiser des tokens, utiliser
        get_paragraphe_boi() à la place.

    Exemple:
        - get_boi("BOI-CF-IOR-10")
    """
    try:
        identifiant = validate_boi_id(identifiant_juridique)
    except ValueError as e:
        return f"❌ {e}"

    if format not in ("text", "html"):
        return f"❌ Erreur : format doit être 'text' ou 'html' (reçu : {format})."

    try:
        response = await search_vigueur(
            where=f'identifiant_juridique="{identifiant}"',
            limit=1,
        )
        results = response.get("results", [])
        if not results:
            return (
                f"❌ Aucun BOI trouvé avec l'identifiant '{identifiant}'.\n\n"
                f"Vérifications possibles :\n"
                f"  - L'identifiant existe-t-il bien sur bofip.impots.gouv.fr ?\n"
                f"  - Le BOI est-il toujours en vigueur (sinon non couvert) ?\n"
                f"  - Essayez rechercher_bofip() pour explorer."
            )
        return format_boi_full(results[0], format_type=format)
    except BofipAPIError as e:
        return f"❌ {e}"


# ═══════════════════════════════════════════════════════════════════════
# OUTIL 7 — Lecture ciblée d'un paragraphe
# ═══════════════════════════════════════════════════════════════════════

@mcp.tool()
async def get_paragraphe_boi(
    identifiant_juridique: str,
    numero_paragraphe: int,
) -> str:
    """
    Extrait un paragraphe précis d'un BOI.

    Les § BOFiP sont numérotés (1, 10, 20, 30, 40...). Cet outil permet
    de citer précisément un § dans des conclusions ("BOI-CF-IOR-10, § 250")
    sans charger l'intégralité du BOI.

    Args:
        identifiant_juridique: Identifiant BOI (ex: "BOI-CF-IOR-10").
        numero_paragraphe: Numéro du § recherché (ex: 250 pour § 250).

    Returns:
        Texte du § demandé avec son contexte (titre du BOI, permalien).
        Si le § n'existe pas, retourne la liste des numéros de § disponibles.

    Exemple:
        - get_paragraphe_boi("BOI-CF-IOR-10", 250)
    """
    try:
        identifiant = validate_boi_id(identifiant_juridique)
    except ValueError as e:
        return f"❌ {e}"

    if numero_paragraphe < 1:
        return "❌ Erreur : numero_paragraphe doit être ≥ 1."

    try:
        response = await search_vigueur(
            where=f'identifiant_juridique="{identifiant}"',
            select="identifiant_juridique,titre,permalien,contenu",
            limit=1,
        )
        results = response.get("results", [])
        if not results:
            return f"❌ Aucun BOI trouvé avec l'identifiant '{identifiant}'."

        record = results[0]
        contenu = record.get("contenu", "")
        titre = record.get("titre", "")
        permalien = record.get("permalien", "")

        paragraphe = extract_paragraphe(contenu, numero_paragraphe)
        if paragraphe is None:
            available = list_paragraphes_numbers(contenu)
            if not available:
                return f"❌ Aucun § numéroté détecté dans {identifiant}."
            sample = available[:20]
            more = f" (et {len(available) - 20} autres)" if len(available) > 20 else ""
            return (
                f"❌ Paragraphe § {numero_paragraphe} non trouvé dans {identifiant}.\n\n"
                f"§ disponibles : {', '.join(map(str, sample))}{more}"
            )

        header = f"""📄 {identifiant} — § {numero_paragraphe}
═══════════════════════════════════════════════════════════════════════
TITRE : {titre}
PERMALIEN : {permalien}
═══════════════════════════════════════════════════════════════════════

"""
        return header + paragraphe

    except BofipAPIError as e:
        return f"❌ {e}"


# ═══════════════════════════════════════════════════════════════════════
# OUTIL 8 — Navigation arborescente
# ═══════════════════════════════════════════════════════════════════════

@mcp.tool()
async def explorer_bofip(
    serie: Optional[str] = None,
    division: Optional[str] = None,
) -> str:
    """
    Navigue l'arborescence du BOFiP : séries → divisions → BOI.

    Outil polyvalent :
    - Sans paramètre : liste toutes les séries (CF, IR, IS, TVA...) avec leur volume.
    - Avec `serie` : liste les divisions de cette série.
    - Avec `serie` + `division` : liste les BOI dans cette division.

    Args:
        serie: Série BOFiP (ex: "CF" pour contrôle fiscal, "IR" pour impôt sur le revenu).
        division: Division au sein d'une série (ex: "IOR" pour Information du contribuable
            et procédures de rectification).

    Returns:
        - Sans paramètre : liste des séries avec nombre de BOI.
        - Avec serie : liste des divisions avec nombre de BOI.
        - Avec serie + division : liste des BOI dans cette division.

    Exemples:
        - explorer_bofip()  → toutes les séries
        - explorer_bofip(serie="CF")  → divisions du contrôle fiscal
        - explorer_bofip(serie="CF", division="IOR")  → BOI dans CF/IOR
    """
    try:
        # Cas 1 : pas de paramètre → liste des séries
        if not serie:
            response = await facets_vigueur("serie")
            return format_facet_results(response, "serie")

        serie_upper = serie.upper()

        # Cas 2 : série seule → divisions de cette série
        if not division:
            response = await search_vigueur(
                refine=[f"serie:{serie_upper}"],
                group_by="division",
                select="division, count(*) as nombre",
                limit=100,
            )
            results = response.get("results", [])
            if not results:
                return f"❌ Aucune division trouvée pour la série '{serie_upper}'. Vérifiez le code (utilisez explorer_bofip() sans argument pour lister)."

            lines = [f"📂 Divisions de la série {serie_upper}\n", "═" * 60]
            sorted_results = sorted(results, key=lambda x: -x.get("nombre", 0))
            for r in sorted_results:
                div = r.get("division", "?")
                nb = r.get("nombre", 0)
                lines.append(f"  • {div:<10} ({nb} BOI)")
            lines.append("\n💡 Utilisez explorer_bofip(serie=\"{0}\", division=\"...\") pour voir les BOI.".format(serie_upper))
            return "\n".join(lines)

        # Cas 3 : série + division → BOI dans cette division
        division_upper = division.upper()
        response = await search_vigueur(
            refine=[f"serie:{serie_upper}", f"division:{division_upper}"],
            select="identifiant_juridique,titre,debut_de_validite,permalien",
            limit=100,
            order_by="identifiant_juridique",
        )
        results = response.get("results", [])
        total = response.get("total_count", 0)
        if not results:
            return f"❌ Aucun BOI trouvé pour {serie_upper}/{division_upper}."

        lines = [
            f"📂 BOI dans {serie_upper}/{division_upper} — {total} BOI",
            "═" * 70,
        ]
        for r in results:
            ident = r.get("identifiant_juridique", "?")
            titre = r.get("titre", "")
            date = r.get("debut_de_validite", "")
            # Tronquer le titre s'il est trop long
            titre_court = titre[:80] + "…" if len(titre) > 80 else titre
            lines.append(f"\n  📄 {ident}  ({date})")
            lines.append(f"     {titre_court}")

        if total > len(results):
            lines.append(f"\n... et {total - len(results)} BOI supplémentaires (limite 100 par appel).")

        return "\n".join(lines)

    except BofipAPIError as e:
        return f"❌ {e}"


# ═══════════════════════════════════════════════════════════════════════
# OUTIL 9 — Flux BOFiP par période
# ═══════════════════════════════════════════════════════════════════════

@mcp.tool()
async def flux_bofip(
    date_debut: Optional[str] = None,
    date_fin: Optional[str] = None,
    type_fichier: Optional[str] = None,
) -> str:
    """
    Liste les flux BOFiP (publications hebdomadaires) sur une période.

    Les flux sont des fichiers .tgz hebdomadaires recensant les nouveautés
    doctrinales (nouveaux BOI, modifications, retraits). Le stock mensuel
    contient l'intégralité du BOFiP en vigueur à une date.

    Args:
        date_debut: Date de début de la période (YYYY-MM-DD). Optionnel.
        date_fin: Date de fin de la période (YYYY-MM-DD). Optionnel.
        type_fichier: "flux" (hebdomadaire) ou "stock" (mensuel complet).
            Si non précisé, retourne tous types.

    Returns:
        Liste des fichiers avec leur description (nombre de publications,
        nature des changements) et URL de téléchargement officielle.

    Note:
        L'open data DGFiP ne conserve qu'un nombre limité de flux récents
        (typiquement les 6 derniers + le stock mensuel courant). Pour des
        archives plus anciennes, consulter directement bofip.impots.gouv.fr.

    Exemples:
        - flux_bofip()  → tous les flux disponibles
        - flux_bofip(type_fichier="stock")  → uniquement le stock mensuel
        - flux_bofip(date_debut="2026-04-01", date_fin="2026-05-31")
    """
    clauses = []

    if date_debut:
        try:
            datetime.strptime(date_debut, "%Y-%m-%d")
            clauses.append(f"date_de_fin >= date'{date_debut}'")
        except ValueError:
            return f"❌ Erreur : date_debut au format YYYY-MM-DD (reçu : {date_debut})."

    if date_fin:
        try:
            datetime.strptime(date_fin, "%Y-%m-%d")
            clauses.append(f"date_de_debut <= date'{date_fin}'")
        except ValueError:
            return f"❌ Erreur : date_fin au format YYYY-MM-DD (reçu : {date_fin})."

    if type_fichier:
        if type_fichier not in ("flux", "stock"):
            return f"❌ Erreur : type_fichier doit être 'flux' ou 'stock' (reçu : {type_fichier})."
        clauses.append(f'type="{type_fichier}"')

    where = " AND ".join(clauses) if clauses else None

    try:
        response = await search_flux(
            where=where,
            order_by="date_de_fin DESC",
            limit=50,
        )
        return format_flux_results(response)
    except BofipAPIError as e:
        return f"❌ {e}"


# ═══════════════════════════════════════════════════════════════════════
# OUTIL 10 — Extraction des références d'un BOI
# ═══════════════════════════════════════════════════════════════════════

import re as _re

@mcp.tool()
async def extraire_references_boi(identifiant_juridique: str) -> str:
    """
    Extrait toutes les références citées dans un BOI.

    Analyse le contenu d'un BOI pour identifier :
    - Articles CGI cités
    - Articles LPF cités
    - Décisions de jurisprudence citées (CE, Cass.)
    - Autres BOI cités

    Très utile pour cartographier la doctrine et préparer des conclusions :
    permet de voir d'un coup d'œil les fondements textuels et jurisprudentiels
    d'un commentaire administratif.

    Args:
        identifiant_juridique: Identifiant BOI (ex: "BOI-CF-IOR-10").

    Returns:
        Liste structurée des références par catégorie.

    Exemple:
        - extraire_references_boi("BOI-CF-IOR-10-20")
    """
    try:
        identifiant = validate_boi_id(identifiant_juridique)
    except ValueError as e:
        return f"❌ {e}"

    try:
        response = await search_vigueur(
            where=f'identifiant_juridique="{identifiant}"',
            select="identifiant_juridique,titre,contenu,permalien",
            limit=1,
        )
        results = response.get("results", [])
        if not results:
            return f"❌ BOI introuvable : {identifiant}."

        record = results[0]
        contenu = record.get("contenu", "")
        titre = record.get("titre", "")
        permalien = record.get("permalien", "")

        # Extraction par regex
        # Articles CGI : "article 209", "article L. 80 A", "art. 1729"
        articles_cgi = set(_re.findall(
            r'article\s+([LR]?\.?\s*\d+[A-Za-z\s\-]*?)\s+du\s+(?:code\s+général\s+des\s+impôts|CGI)',
            contenu, _re.IGNORECASE
        ))
        articles_lpf = set(_re.findall(
            r'article\s+([LR]?\*?\.?\s*\d+[A-Za-z\s\-]*?)\s+du\s+(?:livre\s+des\s+procédures\s+fiscales|LPF)',
            contenu, _re.IGNORECASE
        ))
        # Décisions CE : "CE, arrêt du 8 mars 2023, n° 463267"
        decisions_ce = set(_re.findall(
            r'CE[,.\s]+(?:arrêt\s+du\s+)?(\d{1,2}\s+\w+\s+\d{4})[,.\s]+(?:n°\s*)?(\d+)',
            contenu, _re.IGNORECASE
        ))
        # Décisions Cass : "Cass. com., 25 juin 2019, n° 17-31.657"
        decisions_cass = set(_re.findall(
            r'Cass[\.\s]+(?:com|civ|crim|soc)[\.,\s]+(?:\d{1,2}\s+\w+\s+\d{4})[,.\s]+n°\s*([\d\-\.]+)',
            contenu, _re.IGNORECASE
        ))
        # Autres BOI cités : "BOI-XX-YY..."
        autres_boi = set(_re.findall(
            r'BOI[\-A-Z0-9]+',
            contenu,
        ))
        # Retirer le BOI lui-même
        autres_boi.discard(identifiant)

        # Format de la réponse
        lines = [
            f"🔗 RÉFÉRENCES de {identifiant}",
            f"   {titre}",
            f"   {permalien}",
            "═" * 70,
        ]

        lines.append(f"\n📜 ARTICLES CGI cités ({len(articles_cgi)})")
        if articles_cgi:
            for a in sorted(articles_cgi):
                lines.append(f"   • article {a.strip()} du CGI")
        else:
            lines.append("   (aucun)")

        lines.append(f"\n📜 ARTICLES LPF cités ({len(articles_lpf)})")
        if articles_lpf:
            for a in sorted(articles_lpf):
                lines.append(f"   • article {a.strip()} du LPF")
        else:
            lines.append("   (aucun)")

        lines.append(f"\n⚖️  JURISPRUDENCE CONSEIL D'ÉTAT ({len(decisions_ce)})")
        if decisions_ce:
            for date, num in sorted(decisions_ce):
                lines.append(f"   • CE, {date}, n° {num}")
        else:
            lines.append("   (aucun)")

        lines.append(f"\n⚖️  JURISPRUDENCE COUR DE CASSATION ({len(decisions_cass)})")
        if decisions_cass:
            for num in sorted(decisions_cass):
                lines.append(f"   • Cass., n° {num}")
        else:
            lines.append("   (aucun)")

        lines.append(f"\n📚 AUTRES BOI cités ({len(autres_boi)})")
        if autres_boi:
            for boi in sorted(autres_boi):
                lines.append(f"   • {boi}")
        else:
            lines.append("   (aucun)")

        lines.append("\n" + "═" * 70)
        lines.append("⚠️  Extraction par analyse textuelle automatique. Vérifier dans le BOI source.")

        return "\n".join(lines)

    except BofipAPIError as e:
        return f"❌ {e}"


# ═══════════════════════════════════════════════════════════════════════
# OUTIL 11 — URL historique d'un BOI
# ═══════════════════════════════════════════════════════════════════════

@mcp.tool()
async def get_url_historique_boi(
    identifiant_juridique: str,
    date: str,
) -> str:
    """
    Construit l'URL de consultation d'un BOI à une date passée.

    En contentieux fiscal, la doctrine opposable est celle en vigueur à la
    date du fait générateur, pas celle d'aujourd'hui. Cet outil génère l'URL
    permettant de consulter un BOI dans sa version historique sur le site
    officiel bofip.impots.gouv.fr.

    ATTENTION : Cet outil ne retourne PAS le contenu historique du BOI
    (l'open data DGFiP ne le permet pas), mais une URL pointant vers
    l'interface du site officiel où la consultation est possible.

    Args:
        identifiant_juridique: Identifiant BOI (ex: "BOI-CF-IOR-10").
        date: Date de consultation souhaitée (YYYY-MM-DD).

    Returns:
        URL officielle de consultation historique + instructions.

    Exemple:
        - get_url_historique_boi("BOI-IR-BASE-10", "2019-06-15")
    """
    try:
        identifiant = validate_boi_id(identifiant_juridique)
    except ValueError as e:
        return f"❌ {e}"

    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        return f"❌ Erreur : date au format YYYY-MM-DD (reçu : {date})."

    # Format BOFiP : BOI-XX-YY-ZZ-AAAAMMJJ
    date_compact = date.replace("-", "")
    url_historique = f"https://bofip.impots.gouv.fr/bofip/{identifiant}-{date_compact}"

    return f"""🕰️  URL HISTORIQUE — {identifiant} au {date}
═══════════════════════════════════════════════════════════════════════

URL : {url_historique}

INSTRUCTIONS :
1. Ouvrir l'URL ci-dessus dans un navigateur.
2. Si la version à cette date existe, elle s'affichera.
3. Si non, le site propose la version la plus proche.
4. Le bandeau supérieur du BOI affiche la date de validité.

LIMITES :
- L'open data DGFiP ne fournit pas le contenu historique structuré.
- Seule l'interface web bofip.impots.gouv.fr permet la consultation à date.
- Pour récupérer la version actuelle, utiliser get_boi("{identifiant}").

ALTERNATIVE :
Si l'URL ne fonctionne pas, essayer :
https://bofip.impots.gouv.fr/bofip/{identifiant}.html
puis utiliser le sélecteur de date intégré au site."""


# ═══════════════════════════════════════════════════════════════════════
# OUTIL 12 — Liste des types de documents BOFiP
# ═══════════════════════════════════════════════════════════════════════

@mcp.tool()
async def lister_types_documents() -> str:
    """
    Liste les types de documents présents dans le BOFiP en vigueur.

    Le BOFiP contient plusieurs catégories de documents :
    - Commentaires administratifs (le gros du corpus)
    - Rescrits de portée générale
    - Actualités doctrinales
    - Barèmes
    - Formulaires
    - Lettres-types
    - Etc.

    Cet outil retourne la liste des types présents dans l'open data avec
    leur volume, ce qui permet de cibler des recherches ultérieures via
    rechercher_avancee_bofip(type_document=...).

    Returns:
        Liste des types avec nombre de documents par type.
    """
    try:
        response = await facets_vigueur("type")
        return format_facet_results(response, "type")
    except BofipAPIError as e:
        return f"❌ {e}"


# ═══════════════════════════════════════════════════════════════════════
# OUTIL 13 — Feedback / ticket
# ═══════════════════════════════════════════════════════════════════════

@mcp.tool()
async def creer_ticket(
    type_ticket: str,
    contenu: str,
) -> str:
    """
    Enregistre un retour utilisateur sur le MCP BOFiP.

    Permet de signaler un bug, suggérer une amélioration ou demander
    un nouvel outil. Les tickets sont enregistrés localement par le serveur
    et peuvent être consultés par le mainteneur.

    Args:
        type_ticket: "bug" (dysfonctionnement), "amelioration" (suggestion),
            ou "feedback" (commentaire général).
        contenu: Description détaillée du retour.

    Returns:
        Confirmation d'enregistrement avec un identifiant de ticket.

    Exemple:
        - creer_ticket("bug", "rechercher_bofip retourne une erreur 500 quand query contient des guillemets")
    """
    type_lower = type_ticket.lower()
    if type_lower not in ("bug", "amelioration", "amélioration", "feedback"):
        return f"❌ Erreur : type_ticket doit être 'bug', 'amelioration' ou 'feedback'."

    # On normalise
    type_normalized = "amelioration" if "amelioration" in type_lower or "amélioration" in type_lower else type_lower

    if not contenu or len(contenu.strip()) < 10:
        return "❌ Erreur : contenu trop court (minimum 10 caractères)."

    # Stockage dans un fichier local (sur Render, ce fichier est éphémère
    # mais permet au moins un log temporaire ; pour un suivi durable il
    # faudrait connecter ce tool à un vrai backend comme un Google Sheet
    # ou un repo GitHub via webhook).
    timestamp = datetime.utcnow().isoformat()
    ticket_id = f"TKT-{timestamp.replace(':', '').replace('-', '').replace('.', '')[:14]}"

    ticket_dir = os.environ.get("BOFIP_MCP_TICKETS_DIR", "/tmp/bofip-mcp-tickets")
    os.makedirs(ticket_dir, exist_ok=True)
    ticket_file = os.path.join(ticket_dir, f"{ticket_id}.txt")
    with open(ticket_file, "w", encoding="utf-8") as f:
        f.write(f"Type: {type_normalized}\n")
        f.write(f"Date: {timestamp}\n")
        f.write(f"---\n{contenu}\n")

    return f"""✅ Ticket enregistré
═══════════════════════════════════════════════════════════════════════
ID : {ticket_id}
Type : {type_normalized}
Date : {timestamp}

Pour un suivi plus structuré, vous pouvez également ouvrir une issue sur
le dépôt GitHub du projet : (à compléter avec votre URL GitHub).
"""


# ═══════════════════════════════════════════════════════════════════════
# Point d'entrée
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Mode HTTP pour déploiement sur Render
    # Render injecte la variable PORT
    port = int(os.environ.get("PORT", 8000))
    mcp.run(transport="http", host="0.0.0.0", port=port)
