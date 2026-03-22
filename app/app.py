import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# hellow
st.set_page_config(layout="wide", page_title="Global Energy Metrics")


@st.cache_data
def load_data():
    energy_file_path = "/home/groot/Documents/College/DV/temp/abhishek/data-viz-group/data/processed/energy_cleaned.csv"
    geo_file_path = "/home/groot/Documents/College/DV/temp/abhishek/data-viz-group/data/processed/country_geo.csv"
    try:
        df_energy = pd.read_csv(energy_file_path)
        df_geo = pd.read_csv(geo_file_path)
    except FileNotFoundError:
        st.error(f"Error: Make sure '{energy_file_path}' and '{geo_file_path}' exist. ")
        st.error(
            "If running locally, adjust file paths accordingly or place the CSVs in the same directory as the script."
        )
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


df_merged_sorted = load_data()

st.title("🌍 Global Energy Metrics Dashboard")
st.markdown(
    "Explore various energy and development metrics across countries over time."
)


def plot_world_map_for_streamlit(df, column_name):
    fig = go.Figure()

    col_data = df[column_name].dropna()
    if col_data.empty:
        st.warning(f"No valid data available for '{column_name}' to plot.")
        return None

    min_val = col_data.min()
    max_val = col_data.max()
    min_year = int(df["Year"].min())
    max_year = int(df["Year"].max())

    for year in range(min_year, max_year + 1):
        filtered_df = df[df["Year"] == year]
        # Always add a trace to maintain index, even if it's empty or mostly NaN
        trace = go.Choropleth(
            locations=filtered_df["Entity"],
            z=filtered_df[column_name],
            locationmode="country names",
            colorscale="Plasma",
            colorbar=dict(title=column_name),
            zmin=min_val,
            zmax=max_val,
            visible=False,
            name=str(year),  # Unique name for each trace
        )
        fig.add_trace(trace)

    # Ensure at least one trace exists before trying to make it visible
    if fig.data:
        fig.data[0].visible = True  # Make the first year visible by default

    steps = []
    for i in range(len(fig.data)):
        year_label = fig.data[i].name
        step = dict(
            method="update",
            args=[
                {"visible": [False] * len(fig.data)},  # Set all traces to invisible
                {"title.text": f"{column_name} Map - {year_label}"},
            ],  # Update title dynamically
            label=year_label,
        )
        step["args"][0]["visible"][i] = True  # Set only the current trace to visible
        steps.append(step)

    sliders = [
        dict(
            active=0,
            steps=steps,
            currentvalue={"prefix": "Year: ", "font": {"size": 14}},
            pad={"t": 50},
        )
    ]

    fig.update_layout(
        title_text=f"{column_name} Map with slider",
        title_font_size=24,
        title_x=0.5,
        geo=dict(showframe=True, showcoastlines=True, projection_type="natural earth"),
        sliders=sliders,
        height=600,
        width=1000,
        font=dict(family="Arial", size=12),
        margin=dict(t=100, l=50, r=50, b=50),
    )
    return fig


# Streamlit UI elements for selecting the column
column_options = [
    "Access to electricity (% of population)",
    "Renewable energy share in the total final energy consumption (%)",
    "Access to clean fuels for cooking",
    "Electricity from fossil fuels (TWh)",
    "Electricity from nuclear (TWh)",
    "Electricity from renewables (TWh)",
    "Low-carbon electricity (% electricity)",
    "Primary energy consumption per capita (kWh/person)",
    "Density(P/Km2)",
    "gdp_per_capita",
]

selected_column = st.selectbox(
    "Select a metric to visualize:",
    column_options,
    index=0,  # Default to the first option
)

if selected_column:
    fig_streamlit = plot_world_map_for_streamlit(df_merged_sorted, selected_column)
    if fig_streamlit:
        st.plotly_chart(fig_streamlit, use_container_width=True)
    else:
        st.info(
            "Select another metric or check data availability for the selected metric."
        )

st.write("---")
st.markdown("Developed using Streamlit and Plotly.")
