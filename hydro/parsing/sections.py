from bs4 import BeautifulSoup

from .mappers import normalize_headers


def parse_department_and_commune(
    soup: BeautifulSoup, payload: dict
) -> tuple[str | None, str | None]:
    dep = None
    dep_select = soup.find("select", {"name": "departement"})
    if dep_select:
        opt = (
            dep_select.find("option", {"value": payload.get("departement")})
            or dep_select.find("option", selected=True)
            or dep_select.find("option")
        )
        if opt:
            dep = opt.get_text(strip=True)

    com = None
    com_select = soup.find("select", {"name": "communeDepartement"})
    if com_select:
        opt = com_select.find(
            "option", {"value": payload.get("communeDepartement")}
        ) or com_select.find("option", selected=True)
        if opt:
            com = opt.get_text(strip=True)

    if not com:
        h3 = soup.find(
            lambda t: t.name == "h3" and "Informations générales" in (t.get_text() or "")
        )
        if h3:
            table = h3.find_next("table")
            if table:
                for tr in table.find_all("tr"):
                    th, td = tr.find("th"), tr.find("td")
                    if th and td and "commune" in " ".join(th.stripped_strings).lower():
                        com = td.get_text(" ", strip=True)
                        break
    return dep, com


def parse_section_kv(soup: BeautifulSoup, title: str) -> dict[str, str]:
    out: dict[str, str] = {}
    h3 = soup.find(lambda t: t.name == "h3" and title in (t.get_text() or ""))
    if not h3:
        return out
    table = h3.find_next("table")
    if not table:
        return out
    for tr in table.find_all("tr"):
        th, td = tr.find("th"), tr.find("td")
        if th and td:
            out[" ".join(th.stripped_strings).strip()] = td.get_text(" ", strip=True)
    return out


def parse_results_rows(soup: BeautifulSoup) -> list[dict]:
    rows: list[dict] = []
    h3 = soup.find(lambda t: t.name == "h3" and "Résultats d'analyses" in (t.get_text() or ""))
    if not h3:
        return rows
    table = h3.find_next("table")
    if not table:
        return rows

    header_tr = table.find("tr")
    headers = [th.get_text(" ", strip=True) for th in header_tr.find_all("th")] if header_tr else []
    headers = normalize_headers(headers)

    for tr in table.find_all("tr")[1:]:
        tds = tr.find_all("td")
        if not tds:
            continue
        vals = [td.get_text(" ", strip=True) for td in tds]
        row = {}
        if headers and len(vals) == len(headers):
            for k, v in zip(headers, vals, strict=False):
                row[k] = v
        else:
            row = {
                "parametre": vals[0] if len(vals) > 0 else "",
                "valeur": vals[1] if len(vals) > 1 else "",
                "limite_qualite": vals[2] if len(vals) > 2 else "",
                "reference_qualite": vals[3] if len(vals) > 3 else "",
            }
        rows.append(row)
    return rows


def extract_communes_block_csv(soup: BeautifulSoup) -> str:
    from .mappers import communes_text_to_csv

    label = soup.find(
        "label", string=lambda x: bool(x) and "Commune(s) et/ou quartier(s) du réseau" in x
    )
    if not label:
        return ""
    span = label.find_next("span")
    if not span:
        return ""
    # reconstruir texto con <br>
    text = "\n".join(s.strip() for s in span.stripped_strings)
    return communes_text_to_csv(text)
