import requests
import urllib3

# Opcional: suprime el warning por verify=False (para pruebas)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# === 0) Parámetros de búsqueda (los usas en el POST)
payload = {
    "methode": "rechercher",
    "idRegion": "11",
    "usd": "AEP",
    "posPLV": "0",
    "departement": "095",
    "communeDepartement": "95176",
    "reseau": "095000386_095",
}

# === 1) Hacer GET inicial y POST de búsqueda
session = requests.Session()
url_get = "https://orobnat.sante.gouv.fr/orobnat/afficherPage.do"
resp_get = session.get(
    url_get, params={"methode": "menu", "usd": "AEP", "idRegion": "11"}, verify=False
)
print("GET status:", resp_get.status_code)

url_post = "https://orobnat.sante.gouv.fr/orobnat/rechercherResultatQualite.do"
headers = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Origin": "https://orobnat.sante.gouv.fr",
    "Referer": resp_get.url,
    "User-Agent": "Mozilla/5.0",
}
resp_post = session.post(url_post, data=payload, headers=headers, verify=False)
print("POST status:", resp_post.status_code)


def main():
    cities = fetch_cities()
    if not cities:
        print("There are no active cities in the 'cities' table.")
        return
