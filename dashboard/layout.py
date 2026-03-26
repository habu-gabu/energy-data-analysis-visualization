import streamlit as st
import pandas as pd
import os
import sys

# Ensure the parent directory is in the path so we can import visuals
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import visuals

# Set page config
st.set_page_config(layout="wide", page_title="Energy Activity Dashboard", page_icon="📊")

# Custom CSS for Dark Modular Dashboard (Matching Image)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Roboto', sans-serif;
        background-color: #2D3436;
    }
    
    .stApp {
        background-color: #2D3436;
        color: #DFE6E9;
    }

    .dashboard-card {
        background-color: #353B48;
        border-radius: 12px;
        padding: 40px 20px 20px 20px;
        border: 1px solid #485460;
        margin-bottom: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }
    
    .metric-label {
        color: #B2BEC3;
        text-transform: uppercase;
        font-size: 0.75rem;
        text-align: center;
        letter-spacing: 2px;
        margin-bottom: 25px;
        margin-top: 0;
        padding-top: 10px;
        font-weight: 700;
        display: block;
    }
    
    /* Optimize Expander Look */
    .streamlit-expanderHeader {
        background-color: transparent !important;
        border: none !important;
        padding-left: 0 !important;
        color: #DFE6E9 !important;
        font-weight: 700 !important;
    }
    .streamlit-expander {
        border: none !important;
        box-shadow: none !important;
        background-color: transparent !important;
    }
    .streamlit-expanderContent {
        padding: 0 !important;
    }
    
    .metric-value-large {
        color: #FF4B4B;
        font-size: 3.5rem;
        font-weight: 700;
        text-align: center;
        margin-top: -10px;
    }
    
    .metric-value-blue { color: #00D2FF; font-size: 2rem; font-weight: 700; text-align: center; }
    .metric-value-amber { color: #FFB800; font-size: 2rem; font-weight: 700; text-align: center; }
    .metric-value-green { color: #00FF41; font-size: 2rem; font-weight: 700; text-align: center; }
    
    /* Hide all sidebar toggle/collapsed control buttons */
    [data-testid="stSidebarCollapseButton"],
    [data-testid="collapsedControl"] {
        display: none;
    }
    
    /* Hide expander toggle icons and disable clicking to keep them fixed */
    .streamlit-expanderHeader {
        pointer-events: none !important;
    }
    .streamlit-expanderIcon {
        display: none !important;
    }

    .main {padding-top: 0rem;}
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    energy_file_path = os.path.join(base_dir, "data", "processed", "energy_cleaned.csv")
    geo_file_path = os.path.join(base_dir, "data", "processed", "country_geo.csv")
    df_energy = pd.read_csv(energy_file_path)
    df_geo = pd.read_csv(geo_file_path)
    df_merged = df_energy.merge(df_geo[["Country", "Continent", "Latitude", "Longitude"]], left_on="Entity", right_on="Country", how="left")
    return df_merged.drop(columns=["Country"]).sort_values(by="Year")

df = load_data()
latest_year = int(df["Year"].max())
df_latest = df[df["Year"] == latest_year]

# --- FILTERS & INTERACTIVITY ---
with st.sidebar:
    st.markdown("### Dashboard Controls")
    
    # Year Selection
    selected_year = st.sidebar.slider("Analysis Year", 2000, 2020, 2020)
    
    # Continent Filtering
    continents = df["Continent"].dropna().unique().tolist()
    selected_continents = st.sidebar.multiselect("Filter by Continents", continents, default=continents)
    
    # Global Metric Selection
    map_metric = st.sidebar.selectbox("Primary Dimension", 
                             ["Access to electricity (% of population)", 
                              "Access to clean fuels for cooking"])
    
    st.write("---")
    # Country Specific Analysis
    target_country = st.sidebar.selectbox("Drill-down: Pentagon Stats", df[df["Continent"].isin(selected_continents)]["Entity"].unique(), index=0)

# Global Filtered Dataframe
df_filtered = df[(df["Year"] == selected_year) & (df["Continent"].isin(selected_continents))]
country_data = df[df["Entity"] == target_country].sort_values("Year") # For history
latest_c_data = df_filtered[df_filtered["Entity"] == target_country]
if latest_c_data.empty:
    latest_c_data = df[df["Entity"] == target_country].tail(1) # Fallback to latest available for that country

# --- HEADER ---
header_html = f'<div style="margin-bottom: 25px; padding: 20px; border-radius: 12px; background-color: #1E1E1E; box-shadow: 0 4px 12px rgba(0,0,0,0.3); border: 1px solid #485460;">' \
              f'<h1 style="text-align: center; color: white; margin: 0; font-size: 2.2rem;">Energy Intelligence Engine</h1>' \
              f'<p style="text-align: center; color: #AAB7B8; font-size: 1rem; margin-top: 5px;">Interactive Analysis of <b>{map_metric}</b> | Year: <b>{selected_year}</b></p>' \
              f'</div>'
st.write(header_html, unsafe_allow_html=True)

# --- ROW 1: KPI (DYNAMIC) & PENTAGON ---
with st.expander("Analytics: Performance & Country Profile", expanded=True):
    col_kpi, col_radar = st.columns([1, 1])
    with col_kpi:
        st.markdown(f'<div class="dashboard-card"> <p class="metric-label">Average {map_metric} ({selected_year})</p>', unsafe_allow_html=True)
        avg_val = df_filtered[map_metric].mean()
        st.plotly_chart(visuals.plot_indicator_circle(avg_val, "", visuals.COLORS["blue"]), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with col_radar:
        st.markdown(f'<div class="dashboard-card"> <p class="metric-label">{target_country} Profile (Pentagon Stats)</p>', unsafe_allow_html=True)
        st.plotly_chart(visuals.plot_country_radar(latest_c_data.iloc[0], df), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

# --- ROW 2: INTERACTIVE MAP ---
with st.expander(f"Geospatial: {map_metric} Distribution", expanded=True):
    st.markdown(f'<div class="dashboard-card"> <p class="metric-label">Global Distribution: {map_metric} ({selected_year})</p>', unsafe_allow_html=True)
    st.plotly_chart(visuals.plot_world_map(df_filtered, map_metric, selected_year), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- ROW 3: PRODUCTION HIERARCHY ---
with st.expander(f"Hierarchy: Global Electricity Production ({selected_year})", expanded=True):
    st.markdown(f'<div class="dashboard-card"> <p class="metric-label">Global Production Hierarchy (Click to Explore)</p>', unsafe_allow_html=True)
    st.plotly_chart(visuals.plot_production_hierarchy(df_filtered, selected_year), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- ROW 4: TREND LINES ---
with st.expander("Evolution: Historical Energy Trends", expanded=True):
    st.markdown(f'<div class="dashboard-card"> <p class="metric-label">Historical Trends & Evolution</p>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["Continent Trends", "Country Evolution"])
    with tab1:
        df_trends = df[df["Continent"].isin(selected_continents)]
        st.plotly_chart(visuals.plot_continent_access_trend(df_trends), use_container_width=True)
    with tab2:
        fig_evol = visuals.plot_line_spark(country_data, map_metric, visuals.COLORS["amber"])
        fig_evol.update_layout(xaxis_visible=True, yaxis_visible=True, height=350, title=f"{target_country}: {map_metric} Over Time")
        st.plotly_chart(fig_evol, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- ROW 5: GLOBAL ENERGY MIX ---
with st.expander("Energy Mix: Global Production Trends (Fossil vs Nuclear vs Renewables)", expanded=True):
    st.markdown(f'<div class="dashboard-card"> <p class="metric-label">Global Electricity Generation Mix (1990 - 2020)</p>', unsafe_allow_html=True)
    st.plotly_chart(visuals.plot_global_energy_mix(df), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- FOOTER: DEEP DIVE ---
with st.expander("Advanced: Critical Access Data Exploration", expanded=True):
    st.markdown(f'<div class="dashboard-card"> <p class="metric-label">Critical Status Analysis (<50%)</p>', unsafe_allow_html=True)
    st.plotly_chart(visuals.plot_low_access_notebook(df_filtered), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
