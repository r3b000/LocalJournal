import streamlit as st
import base64

def get_png_icon(png_file, width=24, height=24):
    """Return PNG icon as HTML string for inline use"""
    try:
        with open(png_file, "rb") as f:
            data = f.read()
        b64 = base64.b64encode(data).decode()
        return f'<img src="data:image/png;base64,{b64}" width="{width}" height="{height}" style="vertical-align: middle; margin-right: 8px;"/>'
    except FileNotFoundError:
        return "⚠️"
# st.markdown(f"{chart_icon} Equity Curve", unsafe_allow_html=True)

def icon_header(icon_path, text, width=42, height=42, level="h3"):
    """Display header with icon using HTML headers"""
    icon = get_png_icon(icon_path, width, height)
    
    # Map markdown levels to HTML tags
    level_map = {
        "###": "h3",
        "##": "h2", 
        "#": "h1",
        "####": "h4"
    }
    
    # Convert markdown to HTML if needed
    html_level = level_map.get(level, level)
    
    # Create HTML header
    html = f"""
    <{html_level} style="display: flex; align-items: center; gap: 10px;">
        {icon}
        <span>{text}</span>
    </{html_level}>
    """
    st.markdown(html, unsafe_allow_html=True)




# HOW TO USE IT:

# # Usage - supports both formats:
# icon_header("icons/chart.png", "Equity Curve", level="###")
# icon_header("icons/chart.png", "Equity Curve", level="h3")

# # =============================================================================
# # ICONS
# # =============================================================================

# chart_icon = get_png_icon("icons/chart.png", 28, 28)

