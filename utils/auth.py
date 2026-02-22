import streamlit as st
import time
import json
import os
import hashlib
from utils.style_utils import load_css, apply_creative_theme
from utils.icon_library import get_icon

USER_DB_PATH = "data/users.json"

def _hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def _load_users():
    if not os.path.exists(USER_DB_PATH):
        # Default admin user with email
        default_db = {"admin": {"password": _hash_password("admin"), "email": "admin@ems.gov"}}
        os.makedirs(os.path.dirname(USER_DB_PATH), exist_ok=True)
        with open(USER_DB_PATH, "w") as f:
            json.dump(default_db, f)
        return default_db
    try:
        with open(USER_DB_PATH, "r") as f:
            return json.load(f)
    except:
        return {}

def _save_users(users):
    os.makedirs(os.path.dirname(USER_DB_PATH), exist_ok=True)
    with open(USER_DB_PATH, "w") as f:
        json.dump(users, f)

def require_login():
    """
    Enforces login validation with Full-Screen UI and Email Recovery.
    """
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        
    if not st.session_state.logged_in:
        load_css()
        apply_creative_theme()
        
        # PREMIUM LOGIN LAYOUT
        st.markdown(
            """
            <style>
                [data-testid="stSidebar"] {display: none;} /* Hide Sidebar */
                [data-testid="stHeader"] {display: none;}
                
                .stApp {
                    background: linear-gradient(rgba(15, 23, 42, 0.8), rgba(15, 23, 42, 0.8)), 
                                url('https://images.unsplash.com/photo-1542744173-8e7e53415bb0?auto=format&fit=crop&q=80&w=2000');
                    background-size: cover;
                    background-position: center;
                }
                
                .login-card {
                    background: rgba(30, 41, 59, 0.7);
                    backdrop-filter: blur(20px);
                    -webkit-backdrop-filter: blur(20px);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 24px;
                    padding: 40px;
                    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
                    max-width: 500px;
                    width: 100%;
                    margin: 0 auto;
                }
                
                .stTabs [data-baseweb="tab-list"] {
                    background: transparent;
                    gap: 15px;
                }
                
                .stTabs [data-baseweb="tab"] {
                    height: 45px;
                    background: rgba(255, 255, 255, 0.05);
                    border-radius: 8px;
                    color: white;
                    padding: 0 20px;
                    border: 1px solid transparent;
                }
                
                .stTabs [aria-selected="true"] {
                    background: var(--accent-blue) !important;
                    border-color: rgba(255, 255, 255, 0.2) !important;
                }
            </style>
            """, 
            unsafe_allow_html=True
        )
        
        users_db = _load_users()
        
        # Centered Container
        st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)
        _, col, _ = st.columns([1, 2, 1])
        with col:
            st.markdown(
                f"""
                <div style="text-align: center; margin-bottom: 30px;">
                    <div style="display: flex; justify-content: center; margin-bottom: 15px;">
                        {get_icon("siren", size=64, color="#ef4444")}
                    </div>
                    <h1 style="margin: 0; color: white; -webkit-text-fill-color: white;">EMS Command Center</h1>
                    <p style="color: #94a3b8; font-size: 1.1rem;">Secure Information System v3.0</p>
                </div>
                """, 
                unsafe_allow_html=True
            )
            
            tab1, tab2, tab3 = st.tabs(["LOG IN", "SIGN UP", "RECOVER ACCESS"])

            # --- LOGIN TAB ---
            with tab1:
                with st.form("login_form"):
                    username = st.text_input("Username")
                    password = st.text_input("Password", type="password")
                    st.markdown(" ")
                    submit = st.form_submit_button("Authenticate Access", use_container_width=True)
                    
                    if submit:
                        if username in users_db and users_db[username]["password"] == _hash_password(password):
                            st.session_state.logged_in = True
                            st.session_state.user = username
                            st.success("Access Granted. Initializing dashboard...")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Invalid credentials. Please try again.")

            # --- SIGN UP TAB ---
            with tab2:
                with st.form("signup_form"):
                    new_user = st.text_input("Choose Username")
                    new_email = st.text_input("Official Email Address")
                    new_pass = st.text_input("Set Password", type="password")
                    confirm_pass = st.text_input("Confirm Password", type="password")
                    st.markdown(" ")
                    submit_signup = st.form_submit_button("Create Official Account", use_container_width=True)
                    
                    if submit_signup:
                        if new_user in users_db:
                            st.error("Username already registered.")
                        elif new_pass != confirm_pass:
                            st.error("Passwords do not match.")
                        elif not new_user or not new_pass or not new_email:
                            st.error("All fields (User, Email, Password) are required.")
                        else:
                            users_db[new_user] = {
                                "password": _hash_password(new_pass),
                                "email": new_email
                            }
                            _save_users(users_db)
                            
                            # Auto-Login
                            st.session_state.logged_in = True
                            st.session_state.user = new_user
                            st.success("Account created successfully! Redirecting...")
                            time.sleep(1)
                            st.rerun()

            # --- RECOVER TAB ---
            with tab3:
                st.info("Enter your registered email to reset your password.")
                with st.form("recover_form"):
                    rec_user = st.text_input("Username")
                    rec_email = st.text_input("Registered Email")
                    new_rec_pass = st.text_input("New Password", type="password")
                    st.markdown(" ")
                    submit_recover = st.form_submit_button("Reset Password via Email Verification", use_container_width=True)
                    
                    if submit_recover:
                        if rec_user in users_db and users_db[rec_user].get("email") == rec_email:
                            users_db[rec_user]["password"] = _hash_password(new_rec_pass)
                            _save_users(users_db)
                            st.success("Identity Verified. Password has been reset. Please log in.")
                        else:
                            st.error("Verification failed. Username and Email do not match our records.")
        
        # Stop execution if not logged in
        st.stop()
        
        # User is logged in
        st.sidebar.markdown(f"**{st.session_state.get('user', 'User')}**")
        if st.sidebar.button("Log Out", type="secondary"):
            st.session_state.logged_in = False
            st.rerun()
            
        return True
