import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# Set page config for a professional dashbord look
st.set_page_config(layout="wide", page_title="Global Energy Metrics Dashboard")

# Custom CSS for better aesthetics
st.markdown("""
    <style>
    .metric-container {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    .stPlotlyChart {
         border: 1px solid #e6e9ef;
         padding: 10px;
         border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)

import os

@st.cache_data
def load_data():
    # Use absolute paths relative to this script's directory
    # Current script is in 'app/', data is in 'data/' at the same level as 'app/'
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    energy_file_path = os.path.join(base_dir, "data", "processed", "energy_cleaned.csv")
    geo_file_path = os.path.join(base_dir, "data", "processed", "country_geo.csv")
    
    try:
        df_energy = pd.read_csv(energy_file_path)
        df_geo = pd.read_csv(geo_file_path)
    except FileNotFoundError:
        st.error(f"Error: Could not find data files.")
        st.info(f"Searched paths:\n- {energy_file_path}\n- {geo_file_path}")
        st.stop()

    df_merged = df_energy.merge(
        df_geo[["Country", "Continent", "Latitude", "Longitude", "geometry_wkt"]],
        left_on="Entity",
        right_on="Country",
        how="left",
    )
    df_merged = df_merged.drop(columns=["Country"])
    df_merged_sorted = df_merged.sort_values(by="Year").copy()
    return df_merged_sorted

df = load_data()

st.title("🌍 Global Energy Metrics Dashboard")
st.markdown("Exploring energy accessibility, consumption, and sustainability across the globe.")

# --- 1. TOP ROW: GLOBAL METRICS ---
st.write("---")
latest_year = df["Year"].max()
df_latest = df[df["Year"] == latest_year]

m1_col, m2_col, m3_col = st.columns(3)

with m1_col:
    with st.container(border=True):
        avg_access = df_latest["Access to electricity (% of population)"].mean()
        st.metric("Global Energy Access", f"{avg_access:.1f}%", help="Average percentage of population with electricity access")

with m2_col:
    with st.container(border=True):
        total_renewables = df_latest["Electricity from renewables (TWh)"].sum()
        st.metric("Total Renewable Energy", f"{total_renewables:,.0f} TWh", help="Latest global renewable electricity production")

with m3_col:
    with st.container(border=True):
        avg_gdp = df_latest["gdp_per_capita"].mean()
        st.metric("Avg. GDP Per Capita", f"${avg_gdp:,.0f}", help="Average GDP per capita across reported entities")

# --- 2. MIDDLE ROW: INTERACTIVE WORLD MAP ---
st.write("---")
st.header("🗺️ Global Geographic Analysis")

def plot_world_map(df, column_name):
    fig = go.Figure()
    col_data = df[column_name].dropna()
    if col_data.empty: return None

    min_val, max_val = col_data.min(), col_data.max()
    years = sorted(df["Year"].unique())

    for year in years:
        filtered_df = df[df["Year"] == year]
        fig.add_trace(go.Choropleth(
            locations=filtered_df["Entity"],
            z=filtered_df[column_name],
            locationmode="country names",
            colorscale="Viridis",
            colorbar=dict(title=column_name),
            zmin=min_val, zmax=max_val,
            visible=(year == latest_year),
            name=str(year)
        ))

    steps = []
    for i, year in enumerate(years):
        step = dict(
            method="update",
            label=str(year),
            args=[{"visible": [j == i for j in range(len(years))]},
                  {"title.text": f"{column_name} - Year {year}"}]
        )
        steps.append(step)

    fig.update_layout(
        sliders=[dict(active=len(years)-1, steps=steps, currentvalue={"prefix": "Year: "}, pad={"t": 50})],
        geo=dict(showlakes=True, lakecolor="rgb(255, 255, 255)", projection_type="natural earth"),
        height=600, margin=dict(t=50, l=0, r=0, b=0)
    )
    return fig

# Alias for backward compatibility with new.py
plot_world_map_for_streamlit = plot_world_map

column_options = [
    "Access to electricity (% of population)",
    "Renewable energy share in the total final energy consumption (%)",
    "Primary energy consumption per capita (kWh/person)",
    "Low-carbon electricity (% electricity)",
    "gdp_per_capita"
]

selected_col = st.selectbox("Select a metric for the map:", column_options)
with st.container(border=True):
    fig_map = plot_world_map(df, selected_col)
    if fig_map:
        st.plotly_chart(fig_map, use_container_width=True)

# --- 3. BOTTOM ROW: HISTORICAL TRENDS & HIERARCHY ---
st.write("---")
trend_col, sunburst_col = st.columns([1, 1])

with trend_col:
    st.header("📈 Historical Energy Trends")
    # Global Trend over years
    df_trend = df.groupby("Year")[["Electricity from fossil fuels (TWh)", "Electricity from renewables (TWh)", "Electricity from nuclear (TWh)"]].sum().reset_index()
    fig_line = px.line(df_trend, x="Year", y=["Electricity from fossil fuels (TWh)", "Electricity from renewables (TWh)", "Electricity from nuclear (TWh)"],
                       title="Global Electricity Source Evolution",
                       labels={"value": "Total TWh", "variable": "Source"},
                       color_discrete_map={"Electricity from fossil fuels (TWh)": "#ef553b", "Electricity from renewables (TWh)": "#00cc96", "Electricity from nuclear (TWh)": "#ab63fa"})
    fig_line.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    with st.container(border=True):
        st.plotly_chart(fig_line, use_container_width=True)

with sunburst_col:
    st.header("📊 Production Hierarchy")
    df_sunburst = df_latest.copy()
    df_melted = df_sunburst.melt(
        id_vars=['Continent', 'Entity'],
        value_vars=['Electricity from fossil fuels (TWh)', 'Electricity from nuclear (TWh)', 'Electricity from renewables (TWh)'],
        var_name='Energy_Source', value_name='TWh'
    )
    df_melted['Energy_Source'] = df_melted['Energy_Source'].str.replace('Electricity from ', '').str.replace(' (TWh)', '', regex=False)
    
    fig_sun = px.sunburst(
        df_melted.dropna(subset=['TWh', 'Continent']),
        path=['Continent', 'Entity', 'Energy_Source'],
        values='TWh', color='Continent',
        title=f'Hierarchy in {latest_year}',
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig_sun.update_layout(margin=dict(t=30, l=0, r=0, b=0))
    with st.container(border=True):
        st.plotly_chart(fig_sun, use_container_width=True)


