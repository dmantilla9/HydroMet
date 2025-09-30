import os
import bcrypt
import streamlit as st
from dotenv import load_dotenv
from supabase import create_client, Client

# ---- Env & Config ----
load_dotenv()
from config import SUPABASE_URL, SUPABASE_KEY  # reuse your existing config

RESET_MASTER_KEY = os.getenv("RESET_MASTER_KEY", "")  # required for password resets

st.set_page_config(page_title="HydroMet", page_icon="💧", layout="wide")

def get_supabase() -> Client:
    """Return a Supabase client using your existing config."""
    return create_client(SUPABASE_URL, SUPABASE_KEY)

# ---- Session ----
if "user" not in st.session_state:
    st.session_state.user = None
if "show_register" not in st.session_state:
    st.session_state.show_register = False
if "show_reset" not in st.session_state:
    st.session_state.show_reset = False

# ---- Sidebar ----
st.sidebar.title("HydroMet 💧")
if st.session_state.user:
    st.sidebar.success(f"Signed in: {st.session_state.user['email']}")
    st.sidebar.page_link("pages/1_Manage.py", label="➕ Manage (add data)")
    st.sidebar.page_link("pages/2_Consult.py", label="🔎 Consult tables")
    if st.sidebar.button("Sign out"):
        st.session_state.user = None
        st.rerun()
else:
    st.sidebar.info("Sign in or register to continue.")

# ---- Header ----
st.markdown("<h1 style='text-align:center'>🌊 HydroMet 🌦️</h1>", unsafe_allow_html=True)

# ---- CSS (center block & tighter columns) ----
st.markdown(
    """
    <style>
    .centered-container { max-width: 1000px; margin: 0 auto; padding: 1rem 1rem 2rem; }
    [data-testid="stHorizontalBlock"] > div { padding-right: 0.75rem; } /* reduce gap */
    </style>
    """,
    unsafe_allow_html=True,
)

# ---- Main content (centered container with two columns) ----
st.markdown('<div class="centered-container">', unsafe_allow_html=True)
left_col, right_col = st.columns([1, 1], gap="small")

# ---------- Left: intro text ----------
with left_col:
    st.subheader("Safe water. Smart weather. One system.")
    st.write(
        """
**HydroMet** est un système qui combine deux principaux volets :

1. **Surveillance de la qualité de l’eau potable**  
   - Vérifie si l’eau du robinet est propre à la consommation humaine.  
   - Utilise des données des réseaux d’eau et des résultats d’analyses.  

2. **Informations météorologiques**  
   - Récupère les prévisions météo quotidiennes de plusieurs villes en Région Parisienne.  
   - Intègre ces données pour les relier à l’état de l’eau et à l’environnement.  

En bref :  
*HydroMet réunit la qualité de l’eau potable et les conditions météorologiques pour offrir une vision claire et actualisée de l’eau et du climat.*
"""
    )

# ---------- Helpers ----------
def bcrypt_hash(pwd: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(pwd.encode("utf-8"), salt).decode("utf-8")

# ---------- Right: auth (login / register / reset) ----------
with right_col:
    spacer, form_area = st.columns([0.2, 1])  # control width of the card
    with form_area:
        with st.container(border=True):
            if not st.session_state.user:

                # ======== LOGIN ========
                if not st.session_state.show_register and not st.session_state.show_reset:
                    st.subheader("Sign in")
                    with st.form("login_form_main", clear_on_submit=False):
                        email = st.text_input("Email", key="login_email")
                        pwd = st.text_input("Password", type="password", key="login_pwd")
                        submit_login = st.form_submit_button("Sign in")

                    if submit_login:
                        if not email or not pwd:
                            st.error("Email and password are required.")
                        else:
                            sb = get_supabase()
                            res = (
                                sb.table("app_users")
                                .select("*")
                                .eq("email", (email or "").strip().lower())
                                .limit(1)
                                .execute()
                            )
                            if not res.data:
                                st.error("Invalid credentials.")
                            else:
                                user = res.data[0]
                                try:
                                    ok = bcrypt.checkpw(
                                        pwd.encode("utf-8"),
                                        user["password_hash"].encode("utf-8"),
                                    )
                                except Exception:
                                    ok = False
                                if ok:
                                    st.session_state.user = {
                                        "id": user["id"],
                                        "email": user["email"],
                                        "is_admin": user.get("is_admin", False),
                                    }
                                    st.success("Signed in successfully.")
                                    st.rerun()
                                else:
                                    st.error("Invalid credentials.")

                # ======== REGISTER ========
                elif st.session_state.show_register and not st.session_state.show_reset:
                    st.subheader("Register")
                    with st.form("register_form_main", clear_on_submit=True):
                        r_email = st.text_input("Email", key="reg_email")
                        r_pwd = st.text_input("Password", type="password", key="reg_pwd")
                        r_pwd2 = st.text_input(
                            "Confirm password", type="password", key="reg_pwd2"
                        )
                        submit_reg = st.form_submit_button("Create account")

                    if submit_reg:
                        if not r_email or not r_pwd:
                            st.error("Email and password are required.")
                        elif r_pwd != r_pwd2:
                            st.error("Passwords do not match.")
                        elif len(r_pwd) < 8:
                            st.error("Password must be at least 8 characters.")
                        else:
                            sb = get_supabase()
                            exists = (
                                sb.table("app_users")
                                .select("id")
                                .eq("email", (r_email or "").strip().lower())
                                .execute()
                            )
                            if exists.data:
                                st.error("Email is already registered.")
                            else:
                                pwd_hash = bcrypt_hash(r_pwd)
                                ins = (
                                    sb.table("app_users")
                                    .insert(
                                        {
                                            "email": (r_email or "").strip().lower(),
                                            "password_hash": pwd_hash,
                                        }
                                    )
                                    .execute()
                                )
                                if ins.data:
                                    st.success("Account created. You can sign in now.")
                                    st.session_state.show_register = False
                                    st.rerun()
                                else:
                                    st.error(
                                        "Could not create the account. Please retry."
                                    )

                # ======== RESET PASSWORD (developer mode with master key) ========
                elif st.session_state.show_reset:
                    st.subheader("Reset password")
                    with st.form("reset_form_main", clear_on_submit=True):
                        r_email = st.text_input("Email", key="reset_email")
                        new_pwd = st.text_input("New password", type="password", key="reset_pwd")
                        new_pwd2 = st.text_input("Confirm new password", type="password", key="reset_pwd2")
                        reset_key = st.text_input("Reset key", type="password", key="reset_key_hint")
                        submit_reset = st.form_submit_button("Update password")

                    if submit_reset:
                        if not r_email or not new_pwd:
                            st.error("Email and new password are required.")
                        elif new_pwd != new_pwd2:
                            st.error("Passwords do not match.")
                        elif len(new_pwd) < 8:
                            st.error("Password must be at least 8 characters.")
                        elif not RESET_MASTER_KEY:
                            st.error("RESET_MASTER_KEY is not configured on the server.")
                        elif reset_key != RESET_MASTER_KEY:
                            st.error("Invalid reset key.")
                        else:
                            sb = get_supabase()
                            # Check user exists
                            res = (
                                sb.table("app_users")
                                .select("id")
                                .eq("email", (r_email or "").strip().lower())
                                .limit(1)
                                .execute()
                            )
                            if not res.data:
                                st.error("No user found with that email.")
                            else:
                                # Hash and update
                                pwd_hash = bcrypt_hash(new_pwd)
                                upd = (
                                    sb.table("app_users")
                                    .update({"password_hash": pwd_hash})
                                    .eq("email", (r_email or "").strip().lower())
                                    .execute()
                                )
                                if upd.data is not None:
                                    st.success("Password updated. You can sign in now.")
                                    st.session_state.show_reset = False
                                    st.session_state.show_register = False
                                    st.rerun()
                                else:
                                    st.error("Could not update the password. Please retry.")

            else:
                st.success("You are signed in.")
                st.write("Use the sidebar to **Manage** data or **Consult** tables.")

        # Toggle buttons (outside the bordered container)
        st.divider()
        if not st.session_state.user:
            cols = st.columns([1, 1])
            with cols[0]:
                if not st.session_state.show_register and not st.session_state.show_reset:
                    if st.button("Create a new account", key="btn_show_register"):
                        st.session_state.show_register = True
                        st.session_state.show_reset = False
                        st.rerun()
                elif st.session_state.show_register:
                    if st.button("⬅ Back to login", key="btn_back_login_from_register"):
                        st.session_state.show_register = False
                        st.rerun()
                elif st.session_state.show_reset:
                    if st.button("⬅ Back to login", key="btn_back_login_from_reset"):
                        st.session_state.show_reset = False
                        st.rerun()

            with cols[1]:
                if not st.session_state.show_reset and not st.session_state.show_register:
                    if st.button("Forgot password?", key="btn_show_reset"):
                        st.session_state.show_reset = True
                        st.rerun()

st.markdown("</div>", unsafe_allow_html=True)  # close centered-container

# ---- Footer ----
st.markdown(
    """
    <style>
    .footer {
        position: fixed; left: 0; bottom: 0; width: 100%;
        text-align: center; padding: 10px; font-size: 14px; color: gray;
        background-color: rgba(255,255,255,0.85); backdrop-filter: blur(2px);
    }
    </style>
    <div class="footer">
        © 2025 Fernando MANTILLA – <a href="https://github.com/dmantilla9" target="_blank">GitHub</a>
    </div>
    """,
    unsafe_allow_html=True,
)
