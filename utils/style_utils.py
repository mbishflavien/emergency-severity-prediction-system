import streamlit as st

def load_css(file_name="assets/style.css"):
    """Load custom CSS styles from file"""
    try:
        with open(file_name, encoding='utf-8') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning(f"CSS file not found: {file_name}")
    except Exception as e:
        st.warning(f"Error loading CSS: {str(e)}")

def apply_creative_theme():
    """Applies the current theme state to the app with smooth transitions."""
    if "theme" not in st.session_state:
        st.session_state.theme = "dark"
    
    if st.session_state.theme == "light":
        st.markdown(
            """
            <style>
                :root {
                    color-scheme: light;
                    /* Brighter, polished light theme to match dark aesthetics */
                    --bg-app: linear-gradient(135deg, #ffffff 0%, #f7fafc 100%);
                    --bg-panel: rgba(255, 255, 255, 0.85);
                    --glass-bg: rgba(255, 255, 255, 0.6);
                    --text-primary: #0b1220;
                    --text-secondary: #475569;
                    --border-subtle: rgba(15, 23, 42, 0.06);
                    --border-focus: rgba(37, 99, 235, 0.18);
                    --accent-primary: #2563eb;
                    --accent-blue: #1e40af;
                    --nav-bg: rgba(255, 255, 255, 0.95);
                    --glass-elevation: 0 6px 18px rgba(16,24,40,0.06);
                }
                body, .stApp { background: var(--bg-app); color: var(--text-primary); }
                .stApp, [data-testid="stSidebar"] { box-shadow: var(--glass-elevation); }
            </style>
            """, 
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            """
            <style>
                :root {
                    color-scheme: dark;
                    --bg-app: linear-gradient(135deg, #0f172a 0%, #1a1f3a 100%);
                    --bg-panel: rgba(15, 23, 42, 0.8);
                    --glass-bg: rgba(30, 41, 59, 0.7);
                    --text-primary: #f1f5f9;
                    --text-secondary: #94a3b8;
                    --border-subtle: rgba(255, 255, 255, 0.1);
                    --accent-primary: #3b82f6;
                    --accent-blue: #3b82f6;
                    --nav-bg: rgba(15, 23, 42, 0.9);
                }
                body, .stApp { background: var(--bg-app); color: #f1f5f9; }
            </style>
            """,
            unsafe_allow_html=True
        )
