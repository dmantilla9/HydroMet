import streamlit as st

st.set_page_config(page_title="Manage - HydroMet", page_icon="🗃️", layout="wide")

# Gate: require login
if "user" not in st.session_state or st.session_state.user is None:
    st.error("You must sign in to access this page.")
    st.stop()

st.title("🗃️ Manage data")

# Reuse your existing forms (no changes to your code)
try:
    from form.hydromet_setup import city_form, water_network_form
except Exception as e:
    st.error(f"Could not import your existing forms: {e}")
    st.stop()

tab1, tab2 = st.tabs(["Add City", "Add Water Network"])

with tab1:
    city_form()

with tab2:
    water_network_form()
