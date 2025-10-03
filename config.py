import os

from dotenv import load_dotenv

load_dotenv()
# Supabase config
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# OpenWatherMap Config
OPENWEATHER_URL = os.getenv("OPENWEATHER_URL")
API_KEY = os.getenv("API_KEY")

# Orobnat config
BASE = os.getenv("BASE_OROBNAT")
URL_GET = os.getenv("URL_OROBNAT_GET")
URL_POST = os.getenv("URL_OROBNAT_POST")

# API data.gouv.fr -- Communes in France
CSV_URL = os.getenv("CSV_URL")
