"""
Advanced Map Utilities for Emergency Response System
Provides optimized map visualization with clustering, custom markers, and interactive controls.
"""

import pandas as pd
import plotly.graph_objects as go
import numpy as np
from typing import Dict, List, Tuple


def create_incident_map(
    df: pd.DataFrame,
    lat_col: str = "lat",
    lon_col: str = "lon",
    severity_col: str = "severity",
    type_col: str = "type",
    status_col: str = "status",
    height: int = 500,
    zoom: int = 11
) -> go.Figure:
    """
    Create an advanced incident map with custom markers and interactivity.
    
    Args:
        df: DataFrame with incident data
        lat_col: Column name for latitude
        lon_col: Column name for longitude
        severity_col: Column name for severity level
        type_col: Column name for incident type
        status_col: Column name for status
        height: Map height in pixels
        zoom: Initial zoom level
    
    Returns:
        Plotly figure object
    """
    # Color mapping for severity
    severity_colors = {
        'Low': '#10b981',
        'Medium': '#f59e0b',
        'High': '#f97316',
        'Critical': '#ef4444'
    }
    
    # Marker symbols for incident types
    type_symbols = {
        'Fire': 'circle',
        'Medical': 'square',
        'Traffic': 'diamond',
        'Crime': 'triangle-up'
    }
    
    # Create figure
    fig = go.Figure()
    
    # Group by severity and type for better visualization
    for severity in ['Low', 'Medium', 'High', 'Critical']:
        severity_data = df[df[severity_col] == severity]
        
        if len(severity_data) == 0:
            continue
        
        # Create hover text with detailed information (vectorized for speed)
        lat_str = severity_data[lat_col].round(4).astype(str)
        lon_str = severity_data[lon_col].round(4).astype(str)
        hover_texts = (
            "<b>"
            + severity_data[type_col].astype(str)
            + " Incident</b><br>"
            + "Severity: "
            + severity_data[severity_col].astype(str)
            + "<br>"
            + "Status: "
            + severity_data[status_col].astype(str)
            + "<br>"
            + "Location: ("
            + lat_str
            + ", "
            + lon_str
            + ")"
        ).tolist()
        
        # Determine marker size based on severity
        size_map = {'Low': 8, 'Medium': 10, 'High': 12, 'Critical': 15}
        marker_size = size_map.get(severity, 10)
        
        # Add trace for this severity level
        fig.add_trace(go.Scattermapbox(
            lat=severity_data[lat_col],
            lon=severity_data[lon_col],
            mode='markers',
            marker=dict(
                size=marker_size,
                color=severity_colors.get(severity, '#9ca3af'),
                opacity=0.8,
                sizemode='diameter'
            ),
            text=hover_texts,
            hovertemplate='%{text}<extra></extra>',
            name=f'{severity} Severity',
            showlegend=True
        ))
    
    # Calculate center point
    center_lat = df[lat_col].mean()
    center_lon = df[lon_col].mean()
    
    # Update layout with dark theme
    fig.update_layout(
        mapbox=dict(
            style="carto-darkmatter",
            center=dict(lat=center_lat, lon=center_lon),
            zoom=zoom
        ),
        height=height,
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        paper_bgcolor="#1f2937",
        plot_bgcolor="#1f2937",
        font=dict(color="#f1f5f9"),
        legend=dict(
            bgcolor="rgba(31, 41, 59, 0.8)",
            bordercolor="#374151",
            borderwidth=1,
            font=dict(color="#f1f5f9", size=11),
            orientation="v",
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        ),
        hoverlabel=dict(
            bgcolor="#1e293b",
            font_size=12,
            font_family="Inter, sans-serif",
            bordercolor="#374151"
        )
    )
    
    return fig


def create_clustered_map(
    df: pd.DataFrame,
    lat_col: str = "lat",
    lon_col: str = "lon",
    severity_col: str = "severity",
    type_col: str = "type",
    cluster_distance: float = 0.01,
    height: int = 500,
    zoom: int = 11
) -> go.Figure:
    """
    Create a map with incident clustering for better performance with many points.
    
    Args:
        df: DataFrame with incident data
        lat_col: Column name for latitude
        lon_col: Column name for longitude
        severity_col: Column name for severity level
        type_col: Column name for incident type
        cluster_distance: Distance threshold for clustering (in degrees)
        height: Map height in pixels
        zoom: Initial zoom level
    
    Returns:
        Plotly figure object
    """
    if df is None or len(df) == 0:
        return go.Figure()

    # Fast grid-based clustering (O(N)) by binning lat/lon into cells.
    # `cluster_distance` remains in degrees for backward compatibility.
    if cluster_distance <= 0:
        cluster_distance = 0.01

    tmp = df[[lat_col, lon_col, severity_col, type_col]].copy()
    tmp["_lat_bin"] = np.floor(tmp[lat_col].astype(float) / float(cluster_distance)).astype(int)
    tmp["_lon_bin"] = np.floor(tmp[lon_col].astype(float) / float(cluster_distance)).astype(int)

    severity_rank = {"Low": 0, "Medium": 1, "High": 2, "Critical": 3}
    rank_to_severity = {v: k for k, v in severity_rank.items()}

    clusters = []
    for (_, _), g in tmp.groupby(["_lat_bin", "_lon_bin"], sort=False):
        sev_counts = g[severity_col].value_counts().to_dict()
        type_counts = g[type_col].value_counts().to_dict()

        ranks = g[severity_col].map(severity_rank).fillna(0).astype(int)
        max_rank = int(ranks.max()) if len(ranks) else 0
        max_sev = rank_to_severity.get(max_rank, "Low")

        clusters.append(
            {
                "lat": float(g[lat_col].mean()),
                "lon": float(g[lon_col].mean()),
                "count": int(len(g)),
                "severity_counts": sev_counts,
                "type_counts": type_counts,
                "max_severity": max_sev,
            }
        )
    
    # Create figure
    fig = go.Figure()
    
    # Color mapping
    severity_colors = {
        'Low': '#10b981',
        'Medium': '#f59e0b',
        'High': '#f97316',
        'Critical': '#ef4444'
    }
    
    # Plot clusters in a single trace (faster than many traces)
    cluster_lats = [c["lat"] for c in clusters]
    cluster_lons = [c["lon"] for c in clusters]
    marker_sizes = [min(10 + c["count"] * 2, 30) for c in clusters]
    marker_colors = [severity_colors.get(c["max_severity"], "#9ca3af") for c in clusters]
    hover_texts = []
    for c in clusters:
        severity_text = ", ".join([f"{k}: {v}" for k, v in c["severity_counts"].items()])
        type_text = ", ".join([f"{k}: {v}" for k, v in c["type_counts"].items()])
        hover_texts.append(
            "<b>Incident Cluster</b><br>"
            + f"Total Incidents: {c['count']}<br>"
            + f"Severity: {severity_text}<br>"
            + f"Types: {type_text}"
        )

    fig.add_trace(
        go.Scattermapbox(
            lat=cluster_lats,
            lon=cluster_lons,
            mode="markers",
            marker=dict(
                size=marker_sizes,
                color=marker_colors,
                opacity=0.7,
                sizemode="diameter",
            ),
            text=hover_texts,
            hovertemplate="%{text}<extra></extra>",
            showlegend=False,
        )
    )
    
    # Calculate center
    center_lat = df[lat_col].mean()
    center_lon = df[lon_col].mean()
    
    # Update layout
    fig.update_layout(
        mapbox=dict(
            style="carto-darkmatter",
            center=dict(lat=center_lat, lon=center_lon),
            zoom=zoom
        ),
        height=height,
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        paper_bgcolor="#1f2937",
        plot_bgcolor="#1f2937",
        font=dict(color="#f1f5f9"),
        hoverlabel=dict(
            bgcolor="#1e293b",
            font_size=12,
            font_family="Inter, sans-serif",
            bordercolor="#374151"
        )
    )
    
    return fig


def get_max_severity(severity_series: pd.Series) -> str:
    """Determine the maximum severity level from a series."""
    severity_order = ['Low', 'Medium', 'High', 'Critical']
    for sev in reversed(severity_order):
        if sev in severity_series.values:
            return sev
    return 'Low'


def filter_incidents(
    df: pd.DataFrame,
    severity_filter: List[str] = None,
    type_filter: List[str] = None,
    status_filter: List[str] = None
) -> pd.DataFrame:
    """
    Filter incidents based on criteria.
    
    Args:
        df: DataFrame with incident data
        severity_filter: List of severity levels to include (None = all)
        type_filter: List of incident types to include (None = all)
        status_filter: List of statuses to include (None = all)
    
    Returns:
        Filtered DataFrame
    """
    filtered = df.copy()
    
    if severity_filter:
        filtered = filtered[filtered['severity'].isin(severity_filter)]
    
    if type_filter:
        filtered = filtered[filtered['type'].isin(type_filter)]
    
    if status_filter:
        filtered = filtered[filtered['status'].isin(status_filter)]
    
    return filtered


def create_map_legend_html() -> str:
    """Create HTML for map legend."""
    return """
    <div style="background-color: rgba(31, 41, 59, 0.9); padding: 15px; border-radius: 8px; border: 1px solid #374151; margin-bottom: 15px;">
        <div style="font-weight: 600; margin-bottom: 10px; color: #f1f5f9;">Severity Levels</div>
        <div style="display: flex; gap: 15px; flex-wrap: wrap;">
            <div style="display: flex; align-items: center; gap: 5px;">
                <div style="width: 12px; height: 12px; border-radius: 50%; background-color: #10b981;"></div>
                <span style="font-size: 0.85rem; color: #cbd5e1;">Low</span>
            </div>
            <div style="display: flex; align-items: center; gap: 5px;">
                <div style="width: 12px; height: 12px; border-radius: 50%; background-color: #f59e0b;"></div>
                <span style="font-size: 0.85rem; color: #cbd5e1;">Medium</span>
            </div>
            <div style="display: flex; align-items: center; gap: 5px;">
                <div style="width: 12px; height: 12px; border-radius: 50%; background-color: #f97316;"></div>
                <span style="font-size: 0.85rem; color: #cbd5e1;">High</span>
            </div>
            <div style="display: flex; align-items: center; gap: 5px;">
                <div style="width: 12px; height: 12px; border-radius: 50%; background-color: #ef4444;"></div>
                <span style="font-size: 0.85rem; color: #cbd5e1;">Critical</span>
            </div>
        </div>
    </div>
    """
