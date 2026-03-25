import streamlit as st
import plotly.express as px
from app import plot_world_map_for_streamlit, load_data

# Set page to wide mode to match a dashboard look
st.set_page_config(layout="wide", page_title="Alternative Energy Dashboard")

df = load_data()
latest_year = df["Year"].max()
df_latest = df[df["Year"] == latest_year]

# --- 1. OUTER FRAME ---
st.title("⚡ Energy Data Dashboard (Alternative Layout)")
st.markdown("A structured view of energy metrics and historical trends.")

# --- 2. TOP ROW (Two Boxes) ---
col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.markdown("### 🔌 Electricity Access")
        avg_access = df_latest["Access to electricity (% of population)"].mean()
        st.metric("Global Average", f"{avg_access:.1f}%")
        st.write("Average percentage of population with access to electricity in the latest recorded year.")

with col2:
    with st.container(border=True):
        st.markdown("### 🏎️ GDP vs Energy")
        avg_gdp = df_latest["gdp_per_capita"].mean()
        st.metric("Avg GDP per Capita", f"${avg_gdp:,.0f}")
        st.write("Average GDP per capita across all entities in the latest recorded year.")

# --- 3. MIDDLE ROW (One Large Box) ---
with st.container(border=True):
    st.markdown("### 🗺️ Interactive Global Map")
    metric = st.selectbox("Select metric for map:", ["Access to electricity (% of population)", "gdp_per_capita"], key="map_select")
    fig = plot_world_map_for_streamlit(df, metric)
    if fig:
        st.plotly_chart(fig, use_container_width=True)

# --- 4. BOTTOM ROW (One Large Box) ---
with st.container(border=True):
    st.markdown("### 📉 Historical Growth Trends")
    # Show growth of low-carbon electricity
    fig_hist = px.area(df.groupby("Year")["Electricity from renewables (TWh)"].sum().reset_index(), 
                       x="Year", y="Electricity from renewables (TWh)",
                       title="Global Renewable Energy Growth Over Time",
                       color_discrete_sequence=["#00cc96"])
    st.plotly_chart(fig_hist, use_container_width=True)