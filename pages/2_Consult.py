import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client, Client
from postgrest.exceptions import APIError

load_dotenv()
from config import SUPABASE_URL, SUPABASE_KEY  # reuse your existing config

st.set_page_config(page_title="Consult - HydroMet", page_icon="🔎", layout="wide")

# ---- Gate: require login ----
if "user" not in st.session_state or st.session_state.user is None:
    st.error("You must sign in to access this page.")
    st.stop()

is_admin = bool(st.session_state.user.get("is_admin", False))

def get_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def safe_query(table: str, search_or: str | None, limit: int, order_candidates: list[str]):
    """
    Execute a query on `table` with OR search and a list of ORDER BY candidates.
    Tries each order column; if it doesn't exist, falls back to the next; finally runs without ORDER.
    """
    sb = get_supabase()

    def build_base():
        q = sb.table(table).select("*").limit(limit)
        if search_or:
            q = q.or_(search_or)
        return q

    last_err = None
    for col in order_candidates:
        try:
            q = build_base().order(col, desc=True)
            return q.execute().data
        except APIError as e:
            # 42703 undefined column
            if getattr(e, "code", None) == "42703" or "does not exist" in (getattr(e, "message", "") or str(e)).lower():
                last_err = e
                continue
            raise
    # no order
    try:
        return build_base().execute().data
    except APIError as e:
        raise last_err or e

st.title("🔎 Consult tables")

# Build tabs dynamically so "Users (admin)" only appears for admins
tab_labels = ["cities", "water_network"] + (["users (admin)"] if is_admin else [])
tabs = st.tabs(tab_labels)

# ===================== cities =====================
with tabs[0]:
    st.subheader("cities")
    c1, c2 = st.columns([2, 1])
    with c1:
        search = st.text_input("Search (postal_code / commune_code / city_name / country / water_code / timezone)")
    with c2:
        limit = st.number_input("Limit", min_value=10, max_value=10000, value=500, step=10)

    search_or = None
    if search:
        like = f"%{search}%"
        search_or = (
            f"postal_code.ilike.{like},"
            f"commune_code.ilike.{like},"
            f"city_name.ilike.{like},"
            f"country.ilike.{like},"
            f"water_code.ilike.{like},"
            f"timezone.ilike.{like}"
        )

    try:
        data = safe_query(
            table="cities",
            search_or=search_or,
            limit=int(limit),
            order_candidates=["inserted_at", "postal_code"],  # your schema
        )
        if data:
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True)
            st.download_button(
                "Download CSV",
                data=df.to_csv(index=False).encode("utf-8"),
                file_name="cities.csv",
                mime="text/csv",
            )
        else:
            st.info("No results.")
    except APIError as e:
        st.error(f"Supabase error (cities): {getattr(e, 'message', str(e))}")
    except Exception as e:
        st.error(f"Unexpected error (cities): {e}")

# ===================== water_network =====================
with tabs[1]:
    st.subheader("water_network")
    c1, c2 = st.columns([2, 1])
    with c1:
        search2 = st.text_input("Search (water_code / water_network_name)", key="wn_s")
    with c2:
        limit2 = st.number_input("Limit", min_value=10, max_value=10000, value=500, step=10, key="wn_l")

    search_or2 = None
    if search2:
        like2 = f"%{search2}%"
        search_or2 = f"water_code.ilike.{like2},water_network_name.ilike.{like2}"

    try:
        data2 = safe_query(
            table="water_network",
            search_or=search_or2,
            limit=int(limit2),
            order_candidates=["water_code"],  # PK in your schema
        )
        if data2:
            df2 = pd.DataFrame(data2)
            st.dataframe(df2, use_container_width=True)
            st.download_button(
                "Download CSV",
                data=df2.to_csv(index=False).encode("utf-8"),
                file_name="water_network.csv",
                mime="text/csv",
            )
        else:
            st.info("No results.")
    except APIError as e:
        st.error(f"Supabase error (water_network): {getattr(e, 'message', str(e))}")
    except Exception as e:
        st.error(f"Unexpected error (water_network): {e}")

# ===================== users (admin only) =====================
if is_admin:
    with tabs[2]:
        st.subheader("users (admin)")
        c1, c2 = st.columns([2, 1])
        with c1:
            search3 = st.text_input("Search (email)")
        with c2:
            limit3 = st.number_input("Limit", min_value=10, max_value=10000, value=500, step=10, key="usr_l")

        search_or3 = None
        if search3:
            like3 = f"%{search3}%"
            # app_users has: email, password_hash, is_admin, created_at (per earlier DDL)
            search_or3 = f"email.ilike.{like3}"

        try:
            # Only show safe columns
            sb = get_supabase()
            q = sb.table("app_users").select("email,is_admin,created_at").limit(int(limit3))
            # order by created_at (if exists), else email
            try:
                q = q.order("created_at", desc=True)
            except Exception:
                q = q.order("email", desc=False)

            if search_or3:
                q = q.or_(search_or3)

            data3 = q.execute().data
            if data3:
                df3 = pd.DataFrame(data3)
                st.dataframe(df3, use_container_width=True)
                st.download_button(
                    "Download CSV",
                    data=df3.to_csv(index=False).encode("utf-8"),
                    file_name="users.csv",
                    mime="text/csv",
                )
            else:
                st.info("No results.")
        except APIError as e:
            st.error(f"Supabase error (users): {getattr(e, 'message', str(e))}")
        except Exception as e:
            st.error(f"Unexpected error (users): {e}")
