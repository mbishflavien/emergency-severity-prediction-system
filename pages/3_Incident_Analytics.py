import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np
from utils.ui_components import load_css, render_header, icon_header
from utils.auth import require_login
from utils.icon_library import get_icon

st.set_page_config(page_title="Analytics | EMS", page_icon="📈", layout="wide")
load_css()
require_login()

# Header
st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 20px;">
        {get_icon("analytics", size=36, color="#10b981")}
        <div>
            <h1 style="margin: 0; font-size: 2rem;">Incident Analytics</h1>
            <p style="margin: 0; color: #94a3b8;">Historical Data Analysis</p>
        </div>
    </div>
    <hr style="border-color: rgba(148, 163, 184, 0.1); margin-bottom: 30px;">
    """, unsafe_allow_html=True)

# Mock Historical Data
dates = pd.date_range(start="2023-01-01", periods=100)
data = pd.DataFrame({
    "Date": dates,
    "Incidents": np.random.randint(10, 50, 100),
    "Response_Time": np.random.normal(8, 2, 100),
    "Severity_Score": np.random.normal(50, 15, 100),
    "Region": np.random.choice(["North", "South", "East", "West"], 100)
})

tab1, tab2, tab3 = st.tabs(["Trends", "Performance", "Heatmaps"])

with tab1:
    icon_header("Monthly Incident Volume", "trending-up", level=3)
    fig = px.bar(data, x="Date", y="Incidents", color="Severity_Score", color_continuous_scale="RdYlGn_r")
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    icon_header("Response Time vs Severity", "clock", level=3)
    fig2 = px.scatter(data, x="Response_Time", y="Severity_Score", color="Region", size="Incidents")
    fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
    st.plotly_chart(fig2, use_container_width=True)

with tab3:
    icon_header("Regional Density", "map", level=3)
    fig3 = px.density_heatmap(data, x="Date", y="Region", z="Incidents", color_continuous_scale="Viridis")
    fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
    st.plotly_chart(fig3, use_container_width=True)
