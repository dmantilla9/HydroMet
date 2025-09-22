import requests
from bs4 import BeautifulSoup
import urllib3

from db.supabase_utils import fetch_cities, insert_analysis

# Opcional: suprime el warning por verify=False (para pruebas)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def main():
    cities = fetch_cities()
    if not cities:
        print("No hay ciudades activas.")
        return

    # Tomamos solo la primera ciudad por ahora
    city = cities[0]
    print("Ciudad seleccionada:", city.get("city_name"))
    print("Ciudad json:", city)

    payload = {
        "methode": "rechercher",
        "idRegion": "11",        # asegúrate que estos nombres coincidan con tu tabla
        "usd": "AEP",
        "posPLV": "0",
        "departement": city.get("water_code")[:3],  # primeros 3 dígitos
        "communeDepartement": city.get("commune_code"),
        "reseau": city.get("water_code"),
    }

    print("Payload generado:", payload)
    session = requests.Session()

    url_post = "https://orobnat.sante.gouv.fr/orobnat/rechercherResultatQualite.do"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://orobnat.sante.gouv.fr",
        "Referer": "https://orobnat.sante.gouv.fr/orobnat/afficherPage.do",
        "User-Agent": "Mozilla/5.0"
    }

    resp_post = session.post(url_post, data=payload, headers=headers, verify=False)
    print("POST status:", resp_post.status_code)
    print("Respuesta:", resp_post.text[:500])  # solo los primeros 500 caracteres

if __name__ == "__main__":
    main()
