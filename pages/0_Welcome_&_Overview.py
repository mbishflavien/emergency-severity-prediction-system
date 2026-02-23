import streamlit as st
from utils.auth import require_login
from utils.ui_components import load_css, icon_header
from utils.icon_library import get_icon, render_icon_html

# Page Configuration
st.set_page_config(
    page_title="System Presentation - EMS Command",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load Custom CSS
load_css()

# Enforce Login
require_login()

# Sidebar branding
st.sidebar.markdown(f"""
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 20px;">
        {get_icon("siren", size=32, color="#ef4444")}
        <h1 style="margin: 0; font-size: 1.5rem;">EMS Command</h1>
    </div>
    """, unsafe_allow_html=True)
st.sidebar.markdown("---")

# Session State for PPT Navigation
if 'current_slide' not in st.session_state:
    st.session_state.current_slide = 0

total_slides = 5

def next_slide():
    if st.session_state.current_slide < total_slides - 1:
        st.session_state.current_slide += 1

def prev_slide():
    if st.session_state.current_slide > 0:
        st.session_state.current_slide -= 1

# PPT Controls Header
c1, c2, c3 = st.columns([1, 4, 1])
with c1:
    if st.session_state.current_slide > 0:
        st.button("Back", on_click=prev_slide, use_container_width=True)
with c3:
    if st.session_state.current_slide < total_slides - 1:
        st.button("Next", on_click=next_slide, use_container_width=True)

# Progress Indicator
progress = (st.session_state.current_slide + 1) / total_slides
st.progress(progress)
st.markdown(f"<div style='text-align: center; color: #64748b; font-size: 0.8rem; margin-top: 5px;'>Slide {st.session_state.current_slide + 1} of {total_slides}</div>", unsafe_allow_html=True)

# Slide Content Rendering
slide = st.session_state.current_slide

if slide == 0:
    # Slide 1: Faith & Foundations
    st.markdown(f"""
        <div style="text-align: center; padding: 100px 40px; background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border-radius: 24px; margin: 40px 0; border: 1px solid #334155; position: relative; overflow: hidden;">
            <div style="position: absolute; top: -50px; right: -50px; opacity: 0.05;">
                {get_icon("target", size=300, color="#ffffff")}
            </div>
            <div style="margin-bottom: 30px;">
                {get_icon("target", size=60, color="#3b82f6")}
            </div>
            <h2 style="font-family: 'Playfair Display', serif; font-style: italic; color: #f1f5f9; font-size: 2.8rem; line-height: 1.3; max-width: 900px; margin: 0 auto; font-weight: 500;">
                "God is our refuge and strength, a very present help in trouble."
            </h2>
            <div style="width: 60px; height: 3px; background: #3b82f6; margin: 30px auto;"></div>
            <p style="color: #94a3b8; font-weight: 700; letter-spacing: 3px; text-transform: uppercase; font-size: 1.1rem;">PSALM 46:1</p>
        </div>
        """, unsafe_allow_html=True)

elif slide == 1:
    # Slide 2: The Vision
    st.markdown("<div style='padding: 40px;'>", unsafe_allow_html=True)
    icon_header("The Vision & Mission", "target", level=1)
    
    col_text, col_img = st.columns([3, 2], gap="large")
    with col_text:
        st.markdown("""
        ### Redefining Emergency Response
        
        The **Emergency Incident Severity Prediction System** is more than just a software tool—it's a critical layer of intelligence 
        for command centers. In moments of crisis, every second counts. Our platform ensures that these seconds are spent 
        executing decisions, not just processing raw data.
        
        #### Strategic Pillars:
        """)
        
        pillars = [
            ("siren", "Accelerated Response", "Reducing the gap between incident detection and unit deployment."),
            ("activity", "Predictive Accuracy", "Using Random Forest ensembles to identify life-threatening situations within milliseconds."),
            ("map", "Geospatial Intelligence", "Mapping incidents against resource availability for optimal dispatch."),
            ("shield", "Operational Resilience", "A robust, data-backed foundation built for mission-critical reliability.")
        ]
        
        for icon, title, desc in pillars:
            st.markdown(f"""
            <div style="display: flex; align-items: flex-start; gap: 15px; margin-bottom: 25px;">
                <div style="background: rgba(59, 130, 246, 0.1); padding: 10px; border-radius: 12px; border: 1px solid rgba(59, 130, 246, 0.2);">
                    {get_icon(icon, size=24, color="#3b82f6")}
                </div>
                <div>
                    <h5 style="margin: 0; color: #f1f5f9;">{title}</h5>
                    <p style="margin: 5px 0 0; color: #94a3b8; font-size: 0.95rem;">{desc}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    with col_img:
        st.image("https://images.unsplash.com/photo-1516733725897-1aa73b87c8e8?auto=format&fit=crop&q=80&w=1000", caption="Strategic Command Control", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

elif slide == 2:
    # Slide 3: Technical Ecosystem
    st.markdown("<div style='padding: 40px;'>", unsafe_allow_html=True)
    icon_header("The Technical Ecosystem", "cpu", level=1)
    
    st.markdown("### System Walkthrough")
    
    # Large UI Flow
    flow_col1, flow_col2, flow_col3, flow_col4 = st.columns(4)
    
    steps = [
        ("camera", "Data Ingestion", "CCTV, Drones, IoT, & Call Center logs enter the secure pipeline.", "#3b82f6"),
        ("activity", "Feature Engineering", "Variables are normalized for the prediction engine.", "#8b5cf6"),
        ("target", "ML Modality", "Random Forest Classifier evaluates severity & confidence scores.", "#f59e0b"),
        ("dispatched", "Dispatch Action", "Visualized alerts are pushed to the nearest response unit.", "#10b981")
    ]
    
    for i, (icon, title, desc, color) in enumerate(steps):
        with [flow_col1, flow_col2, flow_col3, flow_col4][i]:
            st.markdown(f"""
            <div style="background: rgba(30, 41, 59, 0.5); padding: 30px; border-radius: 16px; border: 1px solid #334155; height: 100%; border-top: 4px solid {color};">
                <div style="margin-bottom: 20px;">{get_icon(icon, size=40, color=color)}</div>
                <h4 style="color: #f1f5f9; margin-bottom: 10px;">{title}</h4>
                <p style="color: #94a3b8; font-size: 0.9rem; line-height: 1.5;">{desc}</p>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("###")
    st.info("System optimized for real-time inference with 90%+ model accuracy.")
    st.markdown("</div>", unsafe_allow_html=True)

elif slide == 3:
    # Slide 4: System Modules
    st.markdown("<div style='padding: 40px;'>", unsafe_allow_html=True)
    icon_header("Module Integration", "dashboard", level=1)
    
    st.markdown("Explore the core interface modules designed for field and command operations.")
    
    mod1, mod2, mod3 = st.columns(3, gap="large")
    
    modules = [
        ("dashboard", "Overview Dashboard", "Real-time incident mapping and KPI tracking for strategic awareness.", "dashboard"),
        ("prediction", "Severity Prediction", "Interactive tools for AI-driven assessment of new incoming incidents.", "prediction"),
        ("analytics", "Performance Analytics", "Historical trend analysis to optimize resource allocation strategy.", "analytics")
    ]
    
    for i, (icon, title, desc, link) in enumerate(modules):
        with [mod1, mod2, mod3][i]:
            st.markdown(f"""
            <div style="background: #1e293b; padding: 40px 30px; border-radius: 20px; border: 1px solid #334155; text-align: center;">
                <div style="background: rgba(255, 255, 255, 0.05); width: 80px; height: 80px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 25px;">
                    {get_icon(icon, size=40, color="#f1f5f9")}
                </div>
                <h3 style="color: #f1f5f9; margin-bottom: 15px;">{title}</h3>
                <p style="color: #94a3b8; font-size: 0.95rem; margin-bottom: 25px;">{desc}</p>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown(f"""
    <div style="text-align: center; color: #64748b; font-size: 0.9rem;">
        {render_icon_html("info", size=16, color="#64748b")} &nbsp; EMS Command v2.4 | System Modules
    </div>
    """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

elif slide == 4:
    # Slide 5: Conclusion & Contact
    st.markdown("<div style='padding: 40px; text-align: center;'>", unsafe_allow_html=True)
    
    st.markdown(f"""
<div style="margin-top: 60px; margin-bottom: 40px;">
    {get_icon("resolved", size=80, color="#10b981")}
</div>
<h1 style="color: #f1f5f9; font-size: 3rem; margin-bottom: 20px;">Ready for Dispatch</h1>
<p style="color: #94a3b8; font-size: 1.2rem; max-width: 600px; margin: 0 auto 40px;">
    The Emergency Response System stands ready to support commander operations with real-time intelligence and AI-powered precision.
</p>

<div style="display: flex; justify-content: center; gap: 30px; margin-bottom: 60px;">
    <div style="background: rgba(16, 185, 129, 0.1); padding: 20px 40px; border-radius: 12px; border: 1px solid rgba(16, 185, 129, 0.2);">
        <div style="color: #94a3b8; font-size: 0.8rem; margin-bottom: 5px;">SYSTEM STATUS</div>
        <div style="color: #10b981; font-weight: bold; font-size: 1.1rem;">OPERATIONAL</div>
    </div>
    <div style="background: rgba(59, 130, 246, 0.1); padding: 20px 40px; border-radius: 12px; border: 1px solid rgba(59, 130, 246, 0.2);">
        <div style="color: #94a3b8; font-size: 0.8rem; margin-bottom: 5px;">MODEL VERSION</div>
        <div style="color: #3b82f6; font-weight: bold; font-size: 1.1rem;">v2.4.b-release</div>
    </div>
</div>

<div style="margin-top: 100px; border-top: 1px solid #334155; padding-top: 30px; color: #64748b; font-size: 0.9rem;">
    Managed by OOP Group E | Rwanda Information Society Authority (Mock Integration)
</div>
</div>
""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
