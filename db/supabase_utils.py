# db/supabase_utils.py
# All code, comments, and variables are in English.

from __future__ import annotations

from typing import Any

from supabase import Client, create_client

from config import SUPABASE_KEY, SUPABASE_URL

# ----------------------------
# Supabase client (single global instance)
# ----------------------------
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ----------------------------
# Table names (constants)
# ----------------------------
TBL_CITIES = "cities"
TBL_WEATHER = "weather_data"
TBL_WATER_NETWORK = "water_network"

# New analysis tables (normalized)
TBL_CRITERES = "fait_anl_criteres_recherche"
TBL_INFO = "fait_anl_informations_generales"
TBL_CONF = "fait_anl_conformite"
TBL_RESULTS = "fait_anl_resultats_analyses"


# =====================================================================
# Generic helpers (optional small wrappers for consistency)
# =====================================================================


def _exec_or_raise(op, *, label: str = ""):
    """
    Execute a Supabase operation and return its response.
    If Supabase raises, let it bubble up; callers can catch if needed.
    """
    resp = op.execute()
    # You may add logging here if desired
    return resp


# =====================================================================
# Cities & legacy helpers (kept for compatibility with your app)
# =====================================================================


def fetch_cities() -> list[dict[str, Any]]:
    """Fetch active cities from Supabase."""
    res = _exec_or_raise(
        supabase.table(TBL_CITIES).select("*").eq("active", True), label="fetch_cities"
    )
    return res.data or []


def insert_city(data: dict[str, Any]) -> Any:
    """Insert one city row."""
    try:
        return _exec_or_raise(supabase.table(TBL_CITIES).insert(data), label="insert_city")
    except Exception as e:
        return {"error": str(e)}


def insert_water_network(data: dict[str, Any]) -> Any:
    """Insert one water_network row."""
    try:
        return _exec_or_raise(
            supabase.table(TBL_WATER_NETWORK).insert(data), label="insert_water_network"
        )
    except Exception as e:
        return {"error": str(e)}


def insert_weather(row: dict[str, Any]) -> Any:
    """Insert one weather_data row."""
    return _exec_or_raise(supabase.table(TBL_WEATHER).insert(row), label="insert_weather")


# =====================================================================
# New normalized analysis helpers (4 tables)
# =====================================================================


def upsert_criteres(row: dict[str, Any]) -> Any:
    """
    Upsert into fait_anl_criteres_recherche.
    PK: id (varchar), built as 'dd-mm-aaaa-<code_insee>'.
    Expected keys:
      - id, departement, commune (code INSEE), reseau, communes (CSV from HTML)
    """
    if not row or "id" not in row:
        raise ValueError("upsert_criteres: 'id' is required")
    return _exec_or_raise(
        supabase.table(TBL_CRITERES).upsert(row, on_conflict="id"), label="upsert_criteres"
    )


def upsert_informations(row: dict[str, Any]) -> Any:
    """
    Upsert into fait_anl_informations_generales.
    FK: id -> fait_anl_criteres_recherche(id)
    Expected keys:
      - id, date_prelevement (ISO string), commune_prelevement, installation,
        service_distribution, responsable_distribution, maitre_ouvrage
    """
    if not row or "id" not in row:
        raise ValueError("upsert_informations: 'id' is required")
    return _exec_or_raise(
        supabase.table(TBL_INFO).upsert(row, on_conflict="id"), label="upsert_informations"
    )


def upsert_conformite(row: dict[str, Any]) -> Any:
    """
    Upsert into fait_anl_conformite.
    FK: id -> fait_anl_criteres_recherche(id)
    Expected keys:
      - id, conclusions_sanitaires, conformite_bacteriologique,
        conformite_physico_chimique, respect_references_qualite
    """
    if not row or "id" not in row:
        raise ValueError("upsert_conformite: 'id' is required")
    return _exec_or_raise(
        supabase.table(TBL_CONF).upsert(row, on_conflict="id"), label="upsert_conformite"
    )


def upsert_resultats(rows: list[dict[str, Any]]) -> Any:
    """
    Upsert batch into fait_anl_resultats_analyses.
    PK: (id, parametre)
    Expected keys per row:
      - id, parametre, valeur, limite_qualite, reference_qualite
    """
    if not rows:
        return {"status": "noop", "message": "empty list"}
    # Validate required keys for at least first row
    required = {"id", "parametre"}
    missing = [r for r in rows if not required.issubset(r.keys())]
    if missing:
        raise ValueError("upsert_resultats: each row must include 'id' and 'parametre'")
    return _exec_or_raise(
        supabase.table(TBL_RESULTS).upsert(rows, on_conflict="id,parametre"),
        label="upsert_resultats",
    )


def upsert_all_normalized(
    criteres_row: dict[str, Any],
    informations_row: dict[str, Any],
    conformite_row: dict[str, Any],
    resultats_rows: list[dict[str, Any]],
) -> None:
    """
    Convenience helper: upsert the 4 tables in FK-safe order.
    """
    upsert_criteres(criteres_row)
    upsert_informations(informations_row)
    upsert_conformite(conformite_row)
    if resultats_rows:
        upsert_resultats(resultats_rows)


# =====================================================================
# Small read helpers (useful for debugging)
# =====================================================================


def get_page_exists(page_id: str) -> bool:
    """Return True if a 'criteres' row exists for given id."""
    if not page_id:
        return False
    res = _exec_or_raise(
        supabase.table(TBL_CRITERES).select("id").eq("id", page_id).limit(1),
        label="get_page_exists",
    )
    return bool(res.data)


def get_resultats_for(page_id: str) -> list[dict[str, Any]]:
    """Fetch all result rows for a given id."""
    if not page_id:
        return []
    res = _exec_or_raise(
        supabase.table(TBL_RESULTS).select("*").eq("id", page_id), label="get_resultats_for"
    )
    return res.data or []
