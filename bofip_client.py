"""
Client HTTP pour l'API Opendatasoft du BOFiP.

Gère les appels aux deux datasets :
- bofip-vigueur : contenu doctrinal en vigueur (9 000+ BOI)
- bofip-impots : archives ZIP (stock mensuel + flux hebdomadaires)
"""

import httpx
from typing import Optional, Any
import asyncio
import re

ODS_BASE = "https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets"
DATASET_VIGUEUR = "bofip-vigueur"
DATASET_IMPOTS = "bofip-impots"

# Timeout généreux : l'API peut être lente sur des recherches plein texte profondes
DEFAULT_TIMEOUT = 30.0


class BofipAPIError(Exception):
    """Erreur lors d'un appel à l'API BOFiP."""
    pass


async def _request(path: str, params: dict[str, Any] | None = None) -> dict:
    """Effectue un appel HTTP GET à l'API ODS avec gestion d'erreurs."""
    url = f"{ODS_BASE}/{path}"
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise BofipAPIError(
                f"Erreur API BOFiP ({e.response.status_code}) : "
                f"{e.response.text[:300]}"
            )
        except httpx.RequestError as e:
            raise BofipAPIError(f"Erreur réseau : {e}")
        except Exception as e:
            raise BofipAPIError(f"Erreur inattendue : {e}")


async def search_vigueur(
    where: Optional[str] = None,
    select: Optional[str] = None,
    order_by: Optional[str] = None,
    limit: int = 10,
    offset: int = 0,
    refine: Optional[list[str]] = None,
    group_by: Optional[str] = None,
) -> dict:
    """Recherche dans le dataset bofip-vigueur."""
    params: dict[str, Any] = {"limit": min(limit, 100), "offset": offset}
    if where:
        params["where"] = where
    if select:
        params["select"] = select
    if order_by:
        params["order_by"] = order_by
    if group_by:
        params["group_by"] = group_by
    if refine:
        # ODS attend "refine" répété, mais httpx accepte une liste
        params["refine"] = refine
    return await _request(f"{DATASET_VIGUEUR}/records", params=params)


async def facets_vigueur(facet: str) -> dict:
    """Récupère les valeurs distinctes (et leur count) pour une facette."""
    params = {"facet": facet}
    return await _request(f"{DATASET_VIGUEUR}/facets", params=params)


async def search_flux(
    where: Optional[str] = None,
    order_by: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    """Recherche dans le dataset bofip-impots (flux + stock)."""
    params: dict[str, Any] = {"limit": min(limit, 100), "offset": offset}
    if where:
        params["where"] = where
    if order_by:
        params["order_by"] = order_by
    return await _request(f"{DATASET_IMPOTS}/records", params=params)


def escape_ods_string(s: str) -> str:
    """
    Échappe les apostrophes et guillemets pour les chaînes ODS.
    ODS utilise des doubles guillemets pour les strings.
    """
    return s.replace('"', '\\"')


def build_search_clause(query: str) -> str:
    """Construit une clause search() pour ODS où query est correctement échappé."""
    return f'search("{escape_ods_string(query)}")'


# Identifiant BOI : BOI-SERIE-DIVISION[-XX-YY-ZZ...]
# Exemples : BOI-CF-IOR-10, BOI-IR-BASE-10-20-30, BOI-TVA-DECLA-20-30-20-30
BOI_ID_PATTERN = re.compile(
    r'^BOI(?:-[A-Z0-9]+)+$',
    re.IGNORECASE,
)


def validate_boi_id(identifiant: str) -> str:
    """Valide et normalise un identifiant BOI."""
    identifiant = identifiant.strip().upper()
    if not BOI_ID_PATTERN.match(identifiant):
        raise ValueError(
            f"Identifiant BOI invalide : '{identifiant}'. "
            f"Format attendu : BOI-XX-YY[-ZZ...] (ex: BOI-CF-IOR-10-20)"
        )
    return identifiant
