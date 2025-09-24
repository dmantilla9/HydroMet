# -*- coding: utf-8 -*-
"""
Map parsed DataFrames (meta/info/conf/res) into a single dict
matching the columns of table public.analysis.

Strategy:
- Use French labels (from the page) to fill general/conformity fields.
- Pivot the "Résultats d'analyses" rows by parameter into your fixed columns.
- Store raw text AND, when possible, a numeric value extracted from the result.
"""

from __future__ import annotations
from typing import Dict, Any, Optional
import pandas as pd
import re
import unicodedata


def _norm(s: str) -> str:
    """Lowercase, strip accents, collapse spaces."""
    s = (s or "").strip().lower()
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    s = re.sub(r"\s+", " ", s)
    return s


def _first_float(val: str) -> Optional[float]:
    """
    Extract first float-like number from a result string.
    Handles French decimals (comma), signs and inequalities.
    Examples: '<0,1' -> 0.1 ; '12.34 mg/L' -> 12.34 ; 'nd' -> None
    """
    if not val:
        return None
    # Replace comma with dot for French decimals
    s = val.replace(",", ".")
    m = re.search(r"([-+]?[\d]*\.?[\d]+)", s)
    if not m:
        return None
    try:
        return float(m.group(1))
    except Exception:
        return None


# ---- Label maps -------------------------------------------------------------

# Keys are normalized fragments we expect to find in "Informations générales"
INFO_MAP = {
    "date du prelevement": "date_prelevement",
    "commune de prelevement": "commune_prelevement",
    "installation": "installation",
    "service public de distribution": "service_distribution",
    "service de distribution": "service_distribution",
    "responsable de la distribution": "responsable_distribution",
    "maitre d ouvrage": "maitre_ouvrage",
    "conclusion sanitaire": "conclusion_sanitaire",
    "commentaire": "commentaire",
}

# Keys are normalized fragments for the "Conformité" table
CONF_MAP = {
    "conformite bacteriologique": "conformite_bacteriologique",
    "conformite physico-chimique": "conformite_physico_chimique",
    "respect des references de qualite": "respect_references_qualite",
    "conclusions sanitaires": "conclusion_sanitaire",
}

# Parameter → DB column(s). Keys are normalized fragments looked up in the parameter name.
# For each param we can store `text` (raw) and `value` (float) if applicable.
PARAM_MAP = {
    # Microbiology
    "entero": ("enterocoques_100ml_ms", "enterocoques_100ml_ms_value"),
    "spores sulfito": ("bact_spores_sulfito_redu_100ml", "bact_spores_sulfito_redu_100ml_value"),
    "aerobies revivifiables 22": ("bact_aer_rev_22_68h", "bact_aer_rev_22_68h_value"),
    "aerobies revivifiables 36": ("bact_aer_rev_36_44h", "bact_aer_rev_36_44h_value"),
    "coliformes": ("bacteries_coliformes_100ml_ms", "bacteries_coliformes_100ml_ms_value"),
    "escherichia coli": ("escherichia_coli_100ml_mf", "escherichia_coli_100ml_mf_value"),

    # Field phys-chem
    "temperature": ("temperature_eau_terrain", None),
    "turbidite": ("turbidite_nephelometrique_nfu", None),
    "chlore libre": ("chlore_libre_terrain", None),
    "chlore total": ("chlore_total_terrain", None),
    "ph terrain": ("ph_terrain", None),
    "ph": ("ph", None),
    "conductivite": ("conductivite_25c", None),

    # Chemistry
    "ammonium": ("ammonium_nh4", None),
    "aluminium total": ("aluminium_total", None),

    # Qualitative
    "coloration": ("coloration", None),
    "couleur": ("couleur_qualitatif", None),
    "aspect": ("aspect_qualitatif", None),
    "odeur": ("odeur_qualitatif", None),
    "saveur": ("saveur_qualitatif", None),
    "commentaire": ("commentaire", None),
}


def _find_result_columns(df: pd.DataFrame) -> tuple[str, Optional[str]]:
    """
    Try to identify the parameter and result columns in res_df.
    Returns (param_col, value_col) where value_col is the 'result' text column.
    """
    # Heuristics: look for 'param' and 'result' in headers
    headers = [h for h in df.columns if isinstance(h, str)]
    norm = [_norm(h) for h in headers]

    # Parameter column
    param_col = None
    for i, h in enumerate(norm):
        if "param" in h or "libelle" in h or "substance" in h:
            param_col = headers[i]
            break
    if not param_col and headers:
        param_col = headers[0]  # fallback

    # Result column
    value_col = None
    for i, h in enumerate(norm):
        if "result" in h or "resul" in h or "valeur" in h:
            value_col = headers[i]
            break
    if not value_col and len(headers) > 1:
        value_col = headers[1]  # fallback

    return param_col, value_col


def _map_info_fields(info_df: pd.DataFrame) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if info_df is None or info_df.empty:
        return out
    for col in info_df.columns:
        key_norm = _norm(col)
        val = info_df.iloc[0][col]
        for frag, db_col in INFO_MAP.items():
            if frag in key_norm:
                out[db_col] = val
    return out


def _map_conf_fields(conf_df: pd.DataFrame) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if conf_df is None or conf_df.empty:
        return out
    for col in conf_df.columns:
        key_norm = _norm(col)
        val = conf_df.iloc[0][col]
        for frag, db_col in CONF_MAP.items():
            if frag in key_norm:
                out[db_col] = val
    return out


def _map_results(res_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Transform "Résultats d'analyses" (long form) into fixed DB columns.
    - Stores raw text in *_text columns when schema has them,
      and a numeric value in *_value when applicable.
    """
    out: Dict[str, Any] = {}
    if res_df is None or res_df.empty:
        return out

    param_col, value_col = _find_result_columns(res_df)
    if not param_col or not value_col:
        return out

    for _, row in res_df.iterrows():
        pname = str(row.get(param_col, "")).strip()
        presult = str(row.get(value_col, "")).strip()
        pnorm = _norm(pname)

        for frag, (db_text, db_value) in PARAM_MAP.items():
            if frag in pnorm:
                # Save raw text
                out[db_text] = presult
                # Save numeric if configured or plausible
                num = _first_float(presult)
                if db_value:
                    out[db_value] = num
                else:
                    # If the target column itself is numeric (e.g. pH), try numeric there.
                    # We decide by simple heuristic: if a float exists and target col is not obviously qualitative.
                    if num is not None and not any(q in db_text for q in ("qualitatif", "commentaire")):
                        out[db_text] = num
                break

    return out


def build_analysis_record(
    meta_df: pd.DataFrame,
    info_df: pd.DataFrame,
    conf_df: pd.DataFrame,
    res_df: pd.DataFrame,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Produce a single dict ready for insertion into public.analysis.
    Required NOT NULL fields: departement, commune, reseau.
    """
    record: Dict[str, Any] = {
        "departement": payload.get("departement"),
        "commune": payload.get("communeDepartement"),
        "reseau": payload.get("reseau"),
    }

    # Map general / conformity fields
    record.update(_map_info_fields(info_df))
    record.update(_map_conf_fields(conf_df))

    # Map analysis parameters
    record.update(_map_results(res_df))

    # Optional: parse/normalize date_prelevement to ISO timestamp (if present and parseable)
    if record.get("date_prelevement"):
        try:
            ts = pd.to_datetime(record["date_prelevement"], dayfirst=True, errors="coerce", utc=True)
            if pd.notna(ts):
                record["date_prelevement"] = ts.isoformat()
            else:
                # leave as provided if parsing failed
                pass
        except Exception:
            pass

    return record
