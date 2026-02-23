import streamlit as st
from utils.icon_library import get_icon, render_icon_html

def load_css(file_name="assets/style.css"):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def render_header(title, subtitle=None):
    st.markdown(f"# {title}")
    if subtitle:
        st.markdown(f"### {subtitle}")
    st.markdown("---")

def metric_card(title, value, delta=None, color="white", icon=None):
    """
    Renders a custom metric card using HTML/CSS.
    
    Args:
        title: Card title
        value: Main value to display
        delta: Optional change indicator
        color: Value color
        icon: Optional icon name from icon library
    """
    delta_html = ""
    if delta:
        delta_inversion = "red" if "-" in str(delta) else "green" 
        # Context: Incidents going DOWN is green (good), UP is red (bad) usually. 
        # Or standard: Up is Green. Let's stick to standard financial style green=up unless specified.
        # But for 'Incidents', Up is bad. Let's assume generic usage for now.
        delta_char = "+" if "-" not in str(delta) else ""
        delta_color = "#10b981" if "-" not in str(delta) else "#ef4444"
        delta_html = f'<span style="color: {delta_color}; font-size: 0.9rem; margin-left: 10px;">{delta_char}{delta}</span>'

    icon_html = ""
    if icon:
        icon_svg = get_icon(icon, size=28, color="#64748b")
        icon_html = f'<div style="position: absolute; top: 20px; right: 20px; opacity: 0.3;">{icon_svg}</div>'

    html_code = f"""
    <div class="metric-card" style="position: relative;">
        {icon_html}
        <div style="font-size: 0.9rem; color: #9ca3af; margin-bottom: 5px;">{title}</div>
        <div style="font-size: 2rem; font-weight: bold; color: {color};">
            {value}
            {delta_html}
        </div>
    </div>
    """
    st.markdown(html_code, unsafe_allow_html=True)

def icon_header(text, icon_name, level=3):
    """
    Render a header with an icon.
    
    Args:
        text: Header text
        icon_name: Icon name from icon library
        level: Header level (1-6), default 3
    """
    icon_svg = get_icon(icon_name, size=24, color="#f1f5f9")
    header_tag = f"h{level}"
    st.markdown(
        f"""
        <{header_tag} style="display: flex; align-items: center; gap: 10px; color: #f1f5f9;">
            {icon_svg}
            <span>{text}</span>
        </{header_tag}>
        """,
        unsafe_allow_html=True
    )


def display_severity_badge(level):
    colors = {
        "Low": "rgba(16, 185, 129, 0.2)",
        "Medium": "rgba(245, 158, 11, 0.2)",
        "High": "rgba(249, 115, 22, 0.2)",
        "Critical": "rgba(239, 68, 68, 0.2)" # With red background
    }
    text_colors = {
        "Low": "#10b981",
        "Medium": "#f59e0b",
        "High": "#f97316",
        "Critical": "#ef4444"
    }
    
    bg = colors.get(level, "gray")
    tc = text_colors.get(level, "white")
    
    st.markdown(
        f"""
        <div style="background-color: {bg}; color: {tc}; padding: 8px 16px; border-radius: 20px; text-align: center; font-weight: bold; display: inline-block;">
            {level.upper()} SEVERITY
        </div>
        """,
        unsafe_allow_html=True
    )
