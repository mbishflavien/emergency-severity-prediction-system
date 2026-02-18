"""
Professional SVG Icon Library for Emergency Response System
Provides scalable, customizable icons for the application.
"""

def get_icon(name: str, size: int = 24, color: str = "currentColor") -> str:
    """
    Get an SVG icon by name.
    
    Args:
        name: Icon name (e.g., 'alert', 'dashboard', 'fire')
        size: Icon size in pixels (default: 24)
        color: Icon color (default: currentColor for CSS inheritance)
    
    Returns:
        SVG string ready for rendering
    """
    icons = {
        # Emergency Icons
        'alert': f'''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
            <line x1="12" y1="9" x2="12" y2="13"/>
            <line x1="12" y1="17" x2="12.01" y2="17"/>
        </svg>''',
        
        'siren': f'''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M7 11h10v8a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2v-8Z"/>
            <path d="M12 11V7"/>
            <path d="M12 7c0-2.21-1.79-4-4-4v4"/>
            <path d="M12 7c0-2.21 1.79-4 4-4v4"/>
            <path d="M5 20h14"/>
        </svg>''',
        
        'fire': f'''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"/>
        </svg>''',
        
        'medical': f'''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2v20M2 12h20"/>
            <rect x="6" y="6" width="12" height="12" rx="2"/>
        </svg>''',
        
        'police': f'''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2L2 7l10 5 10-5-10-5z"/>
            <path d="M2 17l10 5 10-5"/>
            <path d="M2 12l10 5 10-5"/>
        </svg>''',
        
        # UI Navigation Icons
        'dashboard': f'''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="3" width="7" height="7"/>
            <rect x="14" y="3" width="7" height="7"/>
            <rect x="14" y="14" width="7" height="7"/>
            <rect x="3" y="14" width="7" height="7"/>
        </svg>''',
        
        'analytics': f'''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="12" y1="20" x2="12" y2="10"/>
            <line x1="18" y1="20" x2="18" y2="4"/>
            <line x1="6" y1="20" x2="6" y2="16"/>
        </svg>''',
        
        'prediction': f'''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/>
            <path d="M12 6v6l4 2"/>
        </svg>''',
        
        'target': f'''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/>
            <circle cx="12" cy="12" r="6"/>
            <circle cx="12" cy="12" r="2"/>
        </svg>''',
        
        'map-pin': f'''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
            <circle cx="12" cy="10" r="3"/>
        </svg>''',
        
        'map': f'''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6"/>
            <line x1="8" y1="2" x2="8" y2="18"/>
            <line x1="16" y1="6" x2="16" y2="22"/>
        </svg>''',
        
        # Status Icons
        'active': f'''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/>
            <circle cx="12" cy="12" r="3" fill="{color}"/>
        </svg>''',
        
        'dispatched': f'''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
        </svg>''',
        
        'resolved': f'''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
            <polyline points="22 4 12 14.01 9 11.01"/>
        </svg>''',
        
        'critical': f'''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>''',
        
        # Resource Icons
        'ambulance': f'''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 17h2l.621-1.862A2 2 0 0 1 7.516 14h8.968a2 2 0 0 1 1.895 1.138L19 17h2"/>
            <circle cx="8" cy="17" r="2"/>
            <circle cx="16" cy="17" r="2"/>
            <path d="M14 9h5l2 3v5h-2"/>
            <path d="M3 13V7a2 2 0 0 1 2-2h8"/>
            <path d="M10 5h4"/>
            <path d="M12 3v4"/>
        </svg>''',
        
        'fire-truck': f'''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 17h2"/>
            <circle cx="8" cy="17" r="2"/>
            <circle cx="16" cy="17" r="2"/>
            <path d="M14 17h-4"/>
            <path d="M19 17h2v-6l-3-3h-4"/>
            <path d="M3 11V6a2 2 0 0 1 2-2h8"/>
            <path d="M14 6h3"/>
        </svg>''',
        
        'police-car': f'''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 17h2"/>
            <circle cx="8" cy="17" r="2"/>
            <circle cx="16" cy="17" r="2"/>
            <path d="M14 17h-4"/>
            <path d="M19 17h2v-6l-3-3h-4"/>
            <path d="M3 11V8a2 2 0 0 1 2-2h8"/>
            <rect x="7" y="3" width="10" height="3" rx="1"/>
        </svg>''',
        
        # Additional UI Icons
        'activity': f'''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
        </svg>''',
        
        'clock': f'''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/>
            <polyline points="12 6 12 12 16 14"/>
        </svg>''',
        
        'users': f'''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
            <circle cx="9" cy="7" r="4"/>
            <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
            <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
        </svg>''',
        
        'trending-up': f'''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/>
            <polyline points="17 6 23 6 23 12"/>
        </svg>''',
        
        'trending-down': f'''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="23 18 13.5 8.5 8.5 13.5 1 6"/>
            <polyline points="17 18 23 18 23 12"/>
        </svg>''',
        
        'recording': f'''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="{color}" stroke="{color}" stroke-width="2">
            <circle cx="12" cy="12" r="8"/>
        </svg>''',
        
        'camera': f'''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/>
            <circle cx="12" cy="13" r="4"/>
        </svg>''',
    }
    
    return icons.get(name, icons['alert'])  # Default to alert icon if not found


def render_icon_html(name: str, size: int = 24, color: str = "currentColor", css_class: str = "") -> str:
    """
    Render an icon wrapped in a span for easy embedding in Streamlit markdown.
    
    Args:
        name: Icon name
        size: Icon size in pixels
        color: Icon color
        css_class: Additional CSS classes
    
    Returns:
        HTML string with icon wrapped in span
    """
    icon_svg = get_icon(name, size, color)
    return f'<span class="icon-wrapper {css_class}" style="display: inline-flex; align-items: center; vertical-align: middle;">{icon_svg}</span>'


def get_severity_icon(severity: str, size: int = 20) -> str:
    """Get appropriate icon for severity level with color."""
    severity_map = {
        'Low': ('resolved', '#10b981'),
        'Medium': ('alert', '#f59e0b'),
        'High': ('alert', '#f97316'),
        'Critical': ('critical', '#ef4444')
    }
    icon_name, color = severity_map.get(severity, ('alert', '#9ca3af'))
    return get_icon(icon_name, size, color)


def get_incident_type_icon(incident_type: str, size: int = 20, color: str = "currentColor") -> str:
    """Get appropriate icon for incident type."""
    type_map = {
        'Fire': 'fire',
        'Medical': 'medical',
        'Traffic': 'activity',
        'Crime': 'police',
        'Accident': 'alert',
        'Other': 'alert'
    }
    icon_name = type_map.get(incident_type, 'alert')
    return get_icon(icon_name, size, color)


def get_status_icon(status: str, size: int = 20) -> str:
    """Get appropriate icon for status with color."""
    status_map = {
        'Active': ('active', '#ef4444'),
        'Dispatched': ('dispatched', '#f59e0b'),
        'Resolved': ('resolved', '#10b981')
    }
    icon_name, color = status_map.get(status, ('active', '#9ca3af'))
    return get_icon(icon_name, size, color)
