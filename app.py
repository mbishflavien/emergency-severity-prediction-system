import streamlit as st
from utils.auth import require_login
from utils.ui_components import load_css, icon_header
from utils.icon_library import get_icon, render_icon_html

# Page Configuration
st.set_page_config(
    page_title="Emergency Response System",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load Custom CSS
load_css()

# Enforce Login
require_login()

# Sidebar Navigation
st.sidebar.markdown(f"""
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 20px;">
        {get_icon("siren", size=32, color="#ef4444")}
        <h1 style="margin: 0; font-size: 1.5rem;">EMS Command</h1>
    </div>
    """, unsafe_allow_html=True)
st.sidebar.markdown("---")
icon_header("Navigation", "dashboard", level=3)

# User Info
st.sidebar.info(f"User: {st.session_state.get('user', 'Admin')} | Role: Commander")

# Live System Log
st.sidebar.markdown("---")
st.sidebar.markdown(f"""
    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 10px;">
        {get_icon("activity", size=20, color="#3b82f6")}
        <span style="font-weight: 600; color: #e2e8f0;">System Log</span>
    </div>
    """, unsafe_allow_html=True)

log_data = [
    {"time": "22:14:02", "src": "SYS", "msg": "Connection Stabilized", "color": "#10b981"},
    {"time": "22:14:05", "src": "DATA", "msg": "Geo-sync active (Kigali)", "color": "#3b82f6"},
    {"time": "22:14:12", "src": "ML", "msg": "Model v2.4 loaded", "color": "#8b5cf6"},
    {"time": "22:14:15", "src": "NET", "msg": "Latency 14ms", "color": "#f59e0b"},
    {"time": "22:14:18", "src": "AUTH", "msg": "User validated", "color": "#10b981"},
    {"time": "22:15:00", "src": "CRON", "msg": "Auto-backup complete", "color": "#64748b"},
]

with st.sidebar.container(height=160):
    for log in log_data:
        st.markdown(
            f"""
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; margin-bottom: 4px;">
                <span style="color: #64748b;">[{log['time']}]</span>
                <span style="color: {log['color']}; font-weight: bold;">{log['src']}:</span>
                <span style="color: #cbd5e1;">{log['msg']}</span>
            </div>
            """, 
            unsafe_allow_html=True
        )

st.markdown("""
<style>
    /* Hide default streamlit nav to use custom if we wanted, 
       but for now we will use Streamlit's native multipage app behavior 
       which automatically reads from /pages folder. 
       So this file mainly serves as a landing or redirection page. */
</style>
""", unsafe_allow_html=True)

# Main Title with Icon
st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 30px;">
        {get_icon("siren", size=48, color="#ef4444")}
        <div>
            <h1 style="margin: 0; line-height: 1.2;">Emergency Incident Severity Prediction System</h1>
            <p style="margin: 0; color: #94a3b8; font-size: 1.1rem;">AI-Powered Command & Control Interface</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.write("Please select a module from the sidebar to begin.")

# Dashboard Summary Integration (Mini-view)
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Active Incidents", "14", "+2")
with col2:
    st.metric("Avg Response Time", "4m 12s", "-30s")
with col3:
    st.metric("Units Available", "8/12", "Normal")
with col4:
    st.metric("System Status", "Online", "Stable")

icon_header("Live Surveillance Nexus", "camera", level=3)

# Real-Time Public Feeds (YouTube Live Embeds)
rec_icon = get_icon("recording", size=12, color="#ef4444")
st.markdown(f"""
<style>
    .cctv-grid {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 15px;
        margin-bottom: 20px;
    }}
    .cctv-container {{
        position: relative;
        border: 2px solid #334155;
        border-radius: 8px;
        overflow: hidden;
        background: #000;
        aspect-ratio: 16/9;
    }}
    .cctv-overlay {{
        position: absolute;
        top: 10px;
        left: 10px;
        color: #0f0;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.7rem;
        background: rgba(0,0,0,0.6);
        padding: 4px 8px;
        border-radius: 4px;
        z-index: 2;
        pointer-events: none;
    }}
    .cctv-rec {{
        position: absolute;
        top: 10px;
        right: 10px;
        color: #ef4444;
        font-weight: bold;
        font-size: 0.7rem;
        animation: blink 1s infinite;
        z-index: 2;
        background: rgba(0,0,0,0.6);
        padding: 4px 8px;
        border-radius: 4px;
        pointer-events: none;
        display: flex;
        align-items: center;
        gap: 5px;
    }}
    .cctv-iframe {{
        width: 100%;
        height: 100%;
        border: none;
        transform: scale(1.05); /* Zoom to hide controls */
        pointer-events: none; /* Prevent user interaction for 'security' feel */
    }}
    @keyframes blink {{ 50% {{ opacity: 0; }} }}
</style>

<div class="cctv-grid">
    <!-- Stream 1: Kigali Drone View (High Quality) -->
    <div class="cctv-container">
        <div class="cctv-overlay">CAM-01 | KIGALI AERIAL | LIVE</div>
        <div class="cctv-rec">{rec_icon} LIVE FEED</div>
        <iframe class="cctv-iframe" 
            src="https://www.youtube.com/embed/tIeUo-K429s?autoplay=1&mute=1&controls=0&showinfo=0&modestbranding=1&loop=1&playlist=tIeUo-K429s&start=30" 
            allow="autoplay; encrypted-media">
        </iframe>
    </div>
    <!-- Stream 2: Kigali Downtown Drive (Traffic) -->
    <div class="cctv-container">
        <div class="cctv-overlay">CAM-02 | DOWNTOWN DRIVE | LIVE</div>
        <div class="cctv-rec">{rec_icon} LIVE FEED</div>
        <iframe class="cctv-iframe" 
            src="https://www.youtube.com/embed/3-1A0k54XbC?autoplay=1&mute=1&controls=0&showinfo=0&modestbranding=1&loop=1&playlist=3-1A0k54XbC&start=60" 
            allow="autoplay; encrypted-media">
        </iframe>
    </div>
</div>
""", unsafe_allow_html=True)

# Local Operator Camera Option
with st.expander("Activate Local Operator Feed"):
    st.write("Enable local webcam for on-site monitoring.")
    local_cam = st.camera_input("Operator Cam")
    if local_cam:
        st.success("Local Feed Active - Logging to secure server...")
