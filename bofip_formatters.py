"""
Formatage des réponses BOFiP pour consommation par un LLM.

Convertit les réponses brutes ODS en texte structuré lisible,
avec des en-têtes de résultats et des footers de pagination.
"""

from typing import Any
import re


def format_boi_summary(record: dict, include_extrait: bool = False) -> str:
    """Formate un BOI en résumé (sans contenu intégral)."""
    parts = []
    identifiant = record.get("identifiant_juridique", "N/A")
    titre = record.get("titre", "Sans titre")
    serie = record.get("serie", "?")
    division = record.get("division", "?")
    date_validite = record.get("debut_de_validite", "?")
    type_doc = record.get("type", "?")
    permalien = record.get("permalien", "")

    parts.append(f"📄 **{identifiant}**")
    parts.append(f"   Titre : {titre}")
    parts.append(f"   Série : {serie} | Division : {division} | Type : {type_doc}")
    parts.append(f"   Début de validité : {date_validite}")
    if permalien:
        parts.append(f"   Permalien : {permalien}")

    if include_extrait:
        contenu = record.get("contenu", "")
        if contenu:
            # Premier paragraphe non-vide, max 300 caractères
            premier = next((p.strip() for p in contenu.split("\n") if p.strip() and len(p.strip()) > 20), "")
            if premier:
                extrait = premier[:300] + ("…" if len(premier) > 300 else "")
                parts.append(f"   Extrait : {extrait}")

    return "\n".join(parts)


def format_search_results(
    response: dict,
    page: int,
    page_size: int,
    tool_name: str,
    include_extrait: bool = True,
) -> str:
    """Formate les résultats d'une recherche avec header + footer de pagination."""
    total = response.get("total_count", 0)
    results = response.get("results", [])

    if total == 0:
        return f"❌ Aucun résultat trouvé pour cette recherche.\n\nAstuce : essayez avec des termes plus généraux, ou vérifiez l'orthographe."

    total_pages = (total + page_size - 1) // page_size
    header = f"📊 RÉSULTATS BOFiP - Page {page}/{total_pages} ({total} document(s) au total)\n"
    header += "═" * 70 + "\n"

    body = "\n\n".join(format_boi_summary(r, include_extrait=include_extrait) for r in results)

    footer_parts = ["\n" + "═" * 70]
    if page < total_pages:
        footer_parts.append(f"➡️  Page suivante : appeler {tool_name}(..., page={page + 1})")
    if total > len(results) and page == 1:
        footer_parts.append(f"💡 {total - len(results)} résultats supplémentaires disponibles via pagination.")

    footer = "\n".join(footer_parts)

    return header + body + footer


def format_boi_full(record: dict, format_type: str = "text") -> str:
    """Formate un BOI complet pour lecture détaillée."""
    identifiant = record.get("identifiant_juridique", "N/A")
    titre = record.get("titre", "Sans titre")
    serie = record.get("serie", "?")
    division = record.get("division", "?")
    date_validite = record.get("debut_de_validite", "?")
    type_doc = record.get("type", "?")
    permalien = record.get("permalien", "")

    header = f"""📄 BOI : {identifiant}
═══════════════════════════════════════════════════════════════════════
TITRE : {titre}
SÉRIE : {serie}  |  DIVISION : {division}  |  TYPE : {type_doc}
DÉBUT DE VALIDITÉ : {date_validite}
PERMALIEN OFFICIEL : {permalien}
═══════════════════════════════════════════════════════════════════════

"""

    if format_type == "html":
        contenu = record.get("contenu_html", "")
    else:
        contenu = record.get("contenu", "")

    if not contenu:
        contenu = "[Contenu non disponible]"

    return header + contenu


# Pattern pour identifier le début d'un paragraphe numéroté dans le contenu text
# Les § BOFiP sont numérotés 1, 10, 20, 30... seuls sur une ligne
PARAGRAPHE_PATTERN = re.compile(r'^(\d+)\s*$', re.MULTILINE)


def extract_paragraphe(contenu: str, numero: int) -> str | None:
    """
    Extrait un paragraphe numéroté précis d'un BOI.
    Les § BOFiP sont identifiés par un nombre seul sur une ligne (1, 10, 20...).
    Retourne le texte du § ou None si introuvable.
    """
    # On cherche le numéro exact comme ligne isolée
    lines = contenu.split("\n")
    target = str(numero).strip()

    start_idx = None
    for i, line in enumerate(lines):
        if line.strip() == target:
            start_idx = i + 1
            break

    if start_idx is None:
        return None

    # On collecte les lignes jusqu'au prochain numéro de paragraphe seul
    paragraph_lines = []
    for line in lines[start_idx:]:
        stripped = line.strip()
        # Un autre numéro de paragraphe seul → on s'arrête
        if stripped and stripped.isdigit() and len(stripped) <= 4:
            break
        paragraph_lines.append(line)

    return "\n".join(paragraph_lines).strip()


def list_paragraphes_numbers(contenu: str) -> list[int]:
    """Liste tous les numéros de paragraphes d'un BOI."""
    numbers = []
    for line in contenu.split("\n"):
        stripped = line.strip()
        if stripped and stripped.isdigit() and len(stripped) <= 4:
            try:
                numbers.append(int(stripped))
            except ValueError:
                pass
    return sorted(set(numbers))


def format_facet_results(response: dict, facet_name: str) -> str:
    """Formate les résultats d'une requête de facette (ex: lister les séries)."""
    facets = response.get("facets", [])
    if not facets:
        return f"Aucune facette trouvée pour '{facet_name}'."

    facet_data = next((f for f in facets if f.get("name") == facet_name), None)
    if not facet_data:
        return f"Facette '{facet_name}' non trouvée dans la réponse."

    values = facet_data.get("facets", [])
    if not values:
        return f"Aucune valeur trouvée pour la facette '{facet_name}'."

    lines = [f"📊 Facette '{facet_name}' — {len(values)} valeur(s) distinctes\n"]
    lines.append("═" * 60)
    for v in sorted(values, key=lambda x: -x.get("count", 0)):
        name = v.get("name", "?")
        count = v.get("count", 0)
        lines.append(f"  • {name:<15} ({count} document{'s' if count > 1 else ''})")
    return "\n".join(lines)


def format_flux_results(response: dict) -> str:
    """Formate les résultats d'une recherche de flux hebdomadaires."""
    results = response.get("results", [])
    total = response.get("total_count", 0)

    if total == 0:
        return "❌ Aucun flux trouvé sur cette période."

    lines = [f"📦 FLUX BOFiP — {total} fichier(s) trouvé(s)\n"]
    lines.append("═" * 70)

    for r in results:
        nom = r.get("nom_du_fichier", "?")
        type_f = r.get("type", "?")
        date_deb = r.get("date_de_debut", "")
        date_fin = r.get("date_de_fin", "?")
        contenu = r.get("contenu", "")
        telecharg = r.get("telechargement", "")

        lines.append(f"\n📄 {nom}")
        lines.append(f"   Type : {type_f}")
        if date_deb:
            lines.append(f"   Période : du {date_deb} au {date_fin}")
        else:
            lines.append(f"   Date : {date_fin}")
        if contenu:
            lines.append(f"   Contenu : {contenu}")
        if telecharg:
            lines.append(f"   Téléchargement : {telecharg}")

    lines.append("\n" + "═" * 70)
    lines.append("💡 Les fichiers sont au format .tgz (archive compressée).")
    lines.append("   Pour consulter individuellement les BOI cités dans un flux,")
    lines.append("   utilisez get_boi() avec l'identifiant juridique.")

    return "\n".join(lines)
