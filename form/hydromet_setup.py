import os
import re
import sys

import streamlit as st
from dotenv import load_dotenv
from supabase import Client, create_client

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import SUPABASE_KEY, SUPABASE_URL
from db.supabase_utils import insert_city, insert_water_network

# ============ Setup Supabase ============ #
load_dotenv()

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ============ UI Components ============ #


def to_upper():
    # Convert text to uppercase while typing
    st.session_state.water_network_name = st.session_state.water_network_name.upper()


def city_form():
    st.subheader("🏙️ Add New City")
    with st.form("city_form", clear_on_submit=True):
        postal_code = st.text_input("Postal Code *")
        commune_code = st.text_input("Commune Code *")
        city_name = st.text_input("City Name *")
        country = st.text_input("Country *")
        lat = st.number_input("Latitude *", min_value=-90.0, max_value=90.0, format="%.6f")
        lon = st.number_input("Longitude *", min_value=-180.0, max_value=180.0, format="%.6f")
        water_code = st.text_input("Water Code *")
        timezone = st.text_input("Timezone (e.g. Europe/Paris) *")
        active = st.checkbox("Active", value=True)

        submitted = st.form_submit_button("Add City")

        if submitted:
            if not postal_code or not city_name:
                st.error("⚠️ Postal Code and City Name are required.")
            else:
                data = {
                    "postal_code": postal_code,
                    "commune_code": commune_code,
                    "city_name": city_name,
                    "country": country,
                    "lat": lat,
                    "lon": lon,
                    "water_code": water_code,
                    "timezone": timezone,
                    "active": active,
                }
                response = insert_city(data)
                if "error" in response:
                    st.error(f"❌ Error: {response['error']}")
                else:
                    st.success(f"✅ City '{city_name}' added successfully!")


def water_network_form():
    st.subheader("〰️ Add New Water Network")
    with st.form("water_network_form", clear_on_submit=True):
        water_code = st.text_input("Water Code *")
        water_network_name = st.text_input("Water Network Name")

        submitted = st.form_submit_button("Add Water Network")

        if submitted:
            if not water_code:
                st.error("⚠️ Water Code is required.")
            elif not re.match(r"^[0-9_]+$", water_code):
                st.error("⚠️ Water Code must contain only digits and underscores (_).")
            else:
                data = {
                    "water_code": water_code,
                    "water_network_name": water_network_name or None,
                }
                response = insert_water_network(data)
                if "error" in response:
                    st.error(f"❌ Error: {response['error']}")
                else:
                    st.success(
                        f"✅ Water Network '{water_network_name or water_code}' added successfully!"
                    )


# ============ Main App ============ #
def main():
    st.markdown("<h1 style='text-align: center;'>🌊 HydroMet 🌦️</h1>", unsafe_allow_html=True)

    option = st.selectbox("Select the table to insert data:", ("cities", "water_network"))

    if option == "cities":
        city_form()
    elif option == "water_network":
        water_network_form()

    st.markdown(
        """
    <style>
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        text-align: center;
        padding: 10px;
        font-size: 14px;
        color: gray;
    }
    </style>
    <div class="footer">
        © 2025 Fernando MANTILLA – <a href="https://github.com/dmantilla9" target="_blank">GitHub</a>
    </div>
    """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
