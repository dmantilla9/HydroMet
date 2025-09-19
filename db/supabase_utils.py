from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def fetch_cities():
    """Fetch active cities from Supabase."""
    res = supabase.table("cities").select("*").eq("active", True).execute()
    return res.data or []

def insert_weather(row: dict):
    """Insert one row into weather_data."""
    return supabase.table("weather_data").insert(row).execute()
