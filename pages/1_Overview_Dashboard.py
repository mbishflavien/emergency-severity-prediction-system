import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from utils.ui_components import load_css, render_header, metric_card, icon_header
from utils.auth import require_login
from utils.icon_library import get_icon
from utils.map_utils import (
    create_incident_map, 
    create_clustered_map, 
    filter_incidents, 
    create_map_legend_html
)

st.set_page_config(page_title="Overview | EMS", page_icon="", layout="wide")
load_css()
require_login()

# Mock Data Generation
@st.cache_data
def get_data():
    # Rwanda (Kigali) coordinates
    lat_center = -1.9441
    lon_center = 30.0619
    
    data = pd.DataFrame({
        'lat': np.random.normal(lat_center, 0.04, 150),  # More points for clustering demo
        'lon': np.random.normal(lon_center, 0.04, 150),
        'severity': np.random.choice(['Low', 'Medium', 'High', 'Critical'], 150, p=[0.4, 0.3, 0.2, 0.1]),
        'type': np.random.choice(['Fire', 'Medical', 'Traffic', 'Crime'], 150),
        'status': np.random.choice(['Active', 'Dispatched', 'Resolved'], 150)
    })
    return data

df = get_data()

# Header
st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 20px;">
        {get_icon("dashboard", size=36, color="#3b82f6")}
        <div>
            <h1 style="margin: 0; font-size: 2rem;">Overview Dashboard</h1>
            <p style="margin: 0; color: #94a3b8;">Real-time Situation Awareness</p>
        </div>
    </div>
    <hr style="border-color: rgba(148, 163, 184, 0.1); margin-bottom: 30px;">
    """, unsafe_allow_html=True)

# KPI Row
col1, col2, col3, col4 = st.columns(4)
with col1:
    metric_card("Total Active Incidents", len(df[df['status']!='Resolved']), "+5", icon="activity")
with col2:
    critical_count = len(df[df['severity']=='Critical'])
    metric_card("Critical Alerts", critical_count, "+2" if critical_count > 5 else "-1", color="#ef4444", icon="critical")
with col3:
    metric_card("Avg Response Time", "5.2m", "-12s", icon="clock")
with col4:
    metric_card("Units Deployed", "42", "High Activity", icon="police-car")

st.markdown("###") # Spacer

# Resource Readiness Monitor
icon_header("Resource Status", "trending-up", level=3)
r1, r2, r3 = st.columns(3)
with r1:
    st.caption("Fire Support Units (12/15)")
    st.progress(0.8)
with r2:
    st.caption("Ambulance Fleet (8/12)")
    st.progress(0.66)
with r3:
    st.caption("Police Patrols (22/30)")
    st.progress(0.73)

st.markdown("###") # Spacer

# Color map for severity
color_map = {'Low': '#10b981', 'Medium': '#f59e0b', 'High': '#f97316', 'Critical': '#ef4444'}

# Main Content Grid
row1_col1, row1_col2 = st.columns([2, 1])

with row1_col1:
    # Map Header & Controls
    c_head, c_filt = st.columns([1, 1])
    with c_head:
        icon_header("Live Incident Map", "map", level=3)
    with c_filt:
        # Mini filter for map
        map_view = st.selectbox("Map View", ["Standard", "Clustered"], label_visibility="collapsed")
    
    # Advanced Map Implementation
    if map_view == "Clustered":
        fig_map = create_clustered_map(df, height=450)
    else:
        fig_map = create_incident_map(df, height=450)
        
    st.plotly_chart(fig_map, use_container_width=True)
    
    # Legend
    st.markdown(create_map_legend_html(), unsafe_allow_html=True)

with row1_col2:
    icon_header("Recent Alerts", "alert", level=3)
    recent = df[df['status'] != 'Resolved'].head(8)[['type', 'severity', 'status']]
    
    # Custom HTML Table for style
    table_html = "<div style='background-color: #1e293b; border-radius: 8px; overflow: hidden; border: 1px solid rgba(148, 163, 184, 0.1);'>"
    table_html += "<table style='width:100%; border-collapse: collapse;'>"
    table_html += "<tr style='background-color: #0f172a; border-bottom: 1px solid #334155; color: #9ca3af;'> <th style='padding: 12px; text-align: left;'>Type</th> <th style='padding: 12px; text-align: left;'>Severity</th> <th style='padding: 12px; text-align: left;'>Status</th> </tr>"
    
    for _, row in recent.iterrows():
        sev_color = color_map.get(row['severity'], 'white')
        table_html += (
            f'<tr style="border-bottom: 1px solid #334155;">'
            f'<td style="padding: 12px; color: #e2e8f0;">{row["type"]}</td>'
            f'<td style="padding: 12px; color: {sev_color}; font-weight: 600;">{row["severity"]}</td>'
            f'<td style="padding: 12px; color: #94a3b8;">{row["status"]}</td>'
            f'</tr>'
        )
    table_html += "</table></div>"
    st.markdown(table_html, unsafe_allow_html=True)

st.markdown("###")

# Charts Row
c1, c2 = st.columns(2)
with c1:
    icon_header("Incident Distribution", "analytics", level=3)
    fig_pie = px.pie(df, names='type', hole=0.6, color_discrete_sequence=px.colors.qualitative.Pastel)
    fig_pie.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", 
        plot_bgcolor="rgba(0,0,0,0)", 
        font=dict(color="#e2e8f0"),
        showlegend=True,
        legend=dict(orientation="h", y=-0.1),
        margin=dict(t=20, b=20, l=20, r=20),
        height=300
    )
    st.plotly_chart(fig_pie, use_container_width=True)

with c2:
    icon_header("Severity Trends", "trending-up", level=3)
    # Mock time series
    dates = pd.date_range(end=pd.Timestamp.now(), periods=24, freq='H')
    trend_data = pd.DataFrame({
        'Time': dates,
        'Incidents': np.random.randint(5, 20, 24)
    })
    fig_line = px.line(trend_data, x='Time', y='Incidents', line_shape='spline')
    fig_line.update_traces(line_color='#3b82f6', line_width=3, fill='tozeroy', fillcolor='rgba(59, 130, 246, 0.1)')
    fig_line.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", 
        plot_bgcolor="rgba(0,0,0,0)", 
        font=dict(color="#e2e8f0"), 
        xaxis=dict(showgrid=False, linecolor='#334155'),
        yaxis=dict(showgrid=True, gridcolor='#334155', zeroline=False),
        margin=dict(t=20, b=20, l=10, r=10),
        height=300
    )
    st.plotly_chart(fig_line, use_container_width=True)
