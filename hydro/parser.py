# -*- coding: utf-8 -*-
"""
Parse OROBNAT HTML into pandas DataFrames:
- meta_df: payload echo + resolved labels
- info_df: "Informations générales" (1 row of TH/TD pairs)
- conf_df: "Conformité" (1 row of TH/TD pairs)
- res_df:  "Résultats d'analyses" (N rows, columns depend on page)
"""

from bs4 import BeautifulSoup
import pandas as pd

H3_INFO = "Informations générales"
H3_CONF = "Conformité"
H3_RES  = "Résultats d'analyses"


def _clean(text: str | None) -> str:
    if not text:
        return ""
    return " ".join(text.replace("\xa0", " ").split()).strip()


def _find_table_after_h3(soup: BeautifulSoup, title_contains: str):
    h3 = soup.find(lambda t: t.name == "h3" and title_contains.lower() in (t.get_text() or "").lower())
    return h3.find_next("table") if h3 else None


def _select_label(soup: BeautifulSoup, name: str, value: str | None):
    sel = soup.find("select", {"name": name})
    if not sel:
        return None
    opt = sel.find("option", {"value": value}) if value else None
    if not opt:
        opt = sel.find("option", selected=True) or sel.find("option")
    return _clean(opt.get_text()) if opt else None


def parse_search_page(html: str, payload: dict) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    dep_label = _select_label(soup, "departement", payload.get("departement"))
    com_label = _select_label(soup, "communeDepartement", payload.get("communeDepartement"))

    # Fallback commune from "Informations générales"
    if not com_label:
        t_info = _find_table_after_h3(soup, H3_INFO)
        if t_info:
            for tr in t_info.find_all("tr"):
                th, td = tr.find("th"), tr.find("td")
                if th and td and "commune" in _clean(" ".join(th.stripped_strings)).lower():
                    com_label = _clean(td.get_text(" ", strip=True))
                    break

    # Served communes (optional)
    communes = []
    for p in soup.find_all("p"):
        label = p.find("label")
        if label and "commune" in (label.get_text(strip=True) or "").lower():
            span = p.find("span")
            if span:
                for s in span.stripped_strings:
                    s2 = _clean(s.lstrip("-"))
                    if s2:
                        communes.append(s2)
            break
    communes_df = pd.DataFrame({"commune_servie": communes}) if communes else pd.DataFrame(columns=["commune_servie"])

    # Generic TH/TD table → dict
    def table_to_dict(table_tag) -> dict:
        out = {}
        if not table_tag:
            return out
        for tr in table_tag.find_all("tr"):
            th, td = tr.find("th"), tr.find("td")
            if th and td:
                key = _clean(" ".join(th.stripped_strings))
                val = _clean(td.get_text(" ", strip=True))
                if key:
                    out[key] = val
        return out

    info_df = pd.DataFrame([table_to_dict(_find_table_after_h3(soup, H3_INFO))])
    conf_df = pd.DataFrame([table_to_dict(_find_table_after_h3(soup, H3_CONF))])

    # Analyses table
    res_df = pd.DataFrame()
    t_res = _find_table_after_h3(soup, H3_RES)
    if t_res:
        header_tr = t_res.find("tr")
        headers = [_clean(th.get_text()) for th in header_tr.find_all("th")] if header_tr else []
        rows = []
        for tr in t_res.find_all("tr")[1:] if header_tr else t_res.find_all("tr"):
            tds = tr.find_all("td")
            if not tds:
                continue
            if headers and len(tds) == len(headers):
                row = {headers[i]: _clean(tds[i].get_text(" ", strip=True)) for i in range(len(headers))}
            else:
                row = {f"col_{i+1}": _clean(td.get_text(" ", strip=True)) for i, td in enumerate(tds)}
            if any(v for v in row.values()):
                rows.append(row)
        res_df = pd.DataFrame(rows) if rows else pd.DataFrame()

    meta_df = pd.DataFrame([{
        "departement_value": payload.get("departement"),
        "commune_value": payload.get("communeDepartement"),
        "reseau_value": payload.get("reseau"),
        "departement_label": dep_label,
        "commune_label": com_label,
    }])

    return {
        "meta_df": meta_df,
        "info_df": info_df,
        "conf_df": conf_df,
        "res_df": res_df,
        "communes_df": communes_df,
    }
