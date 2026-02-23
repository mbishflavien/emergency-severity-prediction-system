import streamlit as st
import pandas as pd
from utils.ui_components import load_css, render_header, display_severity_badge, icon_header
from utils.model_loader import model_instance
from utils.auth import require_login
from utils.icon_library import get_icon, get_incident_type_icon, get_severity_icon

st.set_page_config(page_title="Predict | EMS", page_icon=None, layout="wide")
load_css()
require_login()

# Header
st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 20px;">
        {get_icon("prediction", size=36, color="#8b5cf6")}
        <div>
            <h1 style="margin: 0; font-size: 2rem;">Severity Prediction</h1>
            <p style="margin: 0; color: #94a3b8;">AI-Powered Incident Assessment</p>
        </div>
    </div>
    <hr style="border-color: rgba(148, 163, 184, 0.1); margin-bottom: 30px;">
    """, unsafe_allow_html=True)

col_form, col_result = st.columns([1, 1])

with col_form:
    icon_header("Incident Details", "activity", level=3)
    with st.form("prediction_form"):
        incident_type = st.selectbox("Incident Type", ["Fire", "Medical", "Accident", "Crime", "Other"])
        
        c1, c2 = st.columns(2)
        with c1:
            injuries = st.number_input("Reported Injuries", min_value=0, step=1)
            location_risk = st.slider("Location Risk Level (1-10)", 1, 10, 5)
        with c2:
            casualties = st.number_input("Confirmed Casualties", min_value=0, step=1)
            response_time = st.number_input("Est. Response Time (min)", min_value=1, value=5)

        weather = st.selectbox("Weather Condition", ["Clear", "Rain", "Snow", "Fog", "Storm"])
        time_of_day = st.time_input("Time of Incident")
        
        submitted = st.form_submit_button("Analyze Severity")

if submitted:
    # Prepare input dict
    inputs = {
        "incident_type": incident_type,
        "injuries": injuries,
        "casualties": casualties,
        "location_risk": location_risk,
        "response_time": response_time,
        "weather": weather
    }
    
    with st.spinner("Analyzing incident parameters..."):
        result = model_instance.predict(inputs)
    
    with col_result:
        icon_header("Prediction Result", "target", level=3)
        
        # Result Card
        st.markdown(
            """
            <div style="background-color: #1f2937; padding: 20px; border-radius: 10px; border: 1px solid #374151;">
                <h4 style="color: #9ca3af; margin-bottom: 10px;">Predicted Severity Level</h4>
            </div>
            """, 
            unsafe_allow_html=True
        )
        st.markdown("##") # Spacer
        
        # Display large severity icon next to badge
        sev_icon = get_severity_icon(result['severity_level'], size=64)
        c_icon, c_badge = st.columns([1, 3])
        
        with c_icon:
            st.markdown(f"<div style='display: flex; justify-content: center;'>{sev_icon}</div>", unsafe_allow_html=True)
        with c_badge:
            display_severity_badge(result['severity_level'])
        
        st.markdown(f"""
        ###
        <div style="background-color: #1e293b; padding: 20px; border-radius: 8px; margin-top: 20px; border-left: 4px solid #3b82f6;">
            <div style="color: #94a3b8; font-size: 0.9rem; margin-bottom: 5px;">Analysis Confidence</div>
            <div style="font-size: 1.5rem; font-weight: bold; color: #f1f5f9;">{result['confidence_score']}%</div>
        </div>
        
        <div style="margin-top: 20px;">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 10px;">
                {get_icon("dispatched", size=20, color="#f59e0b")}
                <span style="font-weight: 600; color: #f1f5f9;">Recommended Response:</span>
            </div>
            <div style="background-color: rgba(59, 130, 246, 0.1); padding: 15px; border-radius: 8px; color: #e2e8f0; line-height: 1.6;">
                {result['suggested_response']}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.info("System recommendation only. Commander discretion advised.")

else:
    with col_result:
        st.info("Fill out the form to generate a severity prediction.")
        st.image("https://images.unsplash.com/photo-1589939705384-5185137a7f0f?auto=format&fit=crop&q=80&w=1000", caption="AI Analysis Ready", use_container_width=True)
