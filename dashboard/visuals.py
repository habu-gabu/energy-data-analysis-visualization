import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# Color Palette from Image
COLORS = {
    "red": "#FF4B4B",
    "blue": "#00D2FF",
    "amber": "#FFB800",
    "green": "#00FF41",
    "bg": "#262730",
    "paper": "#31333F"
}

def plot_line_spark(df, y_col, color):
    fig = px.line(df, x="Year", y=y_col, markers=True)
    fig.update_traces(line_color=color, line_width=3)
    fig.update_layout(
        height=350, margin={"r":10,"t":50,"l":10,"b":10},
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color="white"),
        xaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.1)")
    )
    return fig

def plot_world_map(df_filtered, metric_name, year):
    # Match notebook color scales
    scale = "Plasma" if "electricity" in metric_name.lower() else "Viridis"
    
    fig = px.choropleth(
        df_filtered,
        locations="Entity",
        locationmode="country names",
        color=metric_name,
        hover_name="Entity",
        color_continuous_scale=scale,
        title=f"{metric_name} by Country in {year}"
    )
    fig.update_geos(
        showframe=False, showcoastlines=False,
        projection_type='equirectangular',
        bgcolor='rgba(0,0,0,0)',
        landcolor="#34495E",
    )
    fig.update_layout(
        height=450, margin={"r":0,"t":50,"l":0,"b":0},
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        coloraxis_showscale=True,
        font=dict(color="white")
    )
    return fig

def plot_continent_access_trend(df):
    # Match notebook logic: Mean by Year and Continent
    df_c_trend = df.groupby(['Year', 'Continent'])['Access to electricity (% of population)'].mean().reset_index()
    fig = px.line(
        df_c_trend, x='Year', y='Access to electricity (% of population)', 
        color='Continent', markers=True,
        title='Average Access to Electricity Over Time by Continent'
    )
    fig.update_layout(
        height=350, margin={"r":10,"t":50,"l":10,"b":10},
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color="white"),
        xaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.1)")
    )
    return fig

def plot_low_access_notebook(df_filtered):
    # Match notebook logic: < 50% access, sorted
    df_low = df_filtered[df_filtered['Access to electricity (% of population)'] < 50].sort_values(by='Access to electricity (% of population)', ascending=True)
    fig = px.bar(
        df_low, x='Access to electricity (% of population)', y='Entity',
        orientation='h', color='Access to electricity (% of population)',
        color_continuous_scale="Reds_r",
        title='Countries with Low Electricity Access (<50%)'
    )
    fig.update_layout(
        height=400, margin={"r":10,"t":50,"l":10,"b":10},
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color="white"),
        yaxis={'categoryorder':'total ascending'}
    )
    return fig

def plot_country_radar(c_data, df_global):
    radar_values = [
        c_data['Access to electricity (% of population)'], 
        c_data['Access to clean fuels for cooking'], 
        c_data['Renewable energy share in the total final energy consumption (%)'], 
        c_data['Low-carbon electricity (% electricity)'], 
        (c_data['gdp_per_capita'] / df_global['gdp_per_capita'].max()) * 100
    ]
    radar_metrics = ['Access', 'Cooking', 'Renewable', 'Low-Carbon', 'GDP']
    
    fig = go.Figure(data=go.Scatterpolar(
        r=radar_values + [radar_values[0]], 
        theta=radar_metrics + [radar_metrics[0]], 
        fill='toself', line_color=COLORS["green"]
    ))
    fig.update_layout(
        polar=dict(
            bgcolor='rgba(0,0,0,0)',
            radialaxis=dict(visible=False, range=[0, 100]),
            angularaxis=dict(gridcolor="rgba(255,255,255,0.1)", linecolor="rgba(255,255,255,0.1)")
        ),
        showlegend=False, height=250, margin=dict(t=20, b=20, l=40, r=40),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig

def plot_indicator_circle(value, title, color):
    # Remove title from Plotly, will use markdown in layout
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = value,
        gauge = {
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "white"},
            'bar': {'color': color},
            'bgcolor': "rgba(0,0,0,0)",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 100], 'color': 'rgba(255,255,255,0.05)'}
            ],
            'threshold': {
                'line': {'color': "white", 'width': 4},
                'thickness': 0.75,
                'value': value
            }
        }
    ))
    fig.update_layout(
        height=220, margin=dict(t=10, b=10, l=40, r=40),
        paper_bgcolor='rgba(0,0,0,0)', font=dict(color="white")
    )
    return fig

def plot_production_hierarchy(df, year):
    # Filter for year
    df_year = df[df["Year"] == year].copy()
    
    # Filter for Top 3 countries per continent to keep the sunburst clean
    top_3_entities = df_year.sort_values(['Continent', 'Total_electricity'], ascending=[True, False]).groupby('Continent').head(3)['Entity'].tolist()
    df_top = df_year[df_year['Entity'].isin(top_3_entities)]

    # We need to melt the energy sources to create a hierarchy for the sunburst
    # Hierarchy: Continent -> Entity -> Energy Source
    df_melted = df_top.melt(
        id_vars=['Continent', 'Entity'],
        value_vars=['Electricity from fossil fuels (TWh)', 'Electricity from nuclear (TWh)', 'Electricity from renewables (TWh)'],
        var_name='Energy_Source',
        value_name='TWh'
    )

    # Clean up naming
    df_melted['Energy_Source'] = df_melted['Energy_Source'].str.replace('Electricity from ', '').str.replace(' (TWh)', '', regex=False)

    # Create the Sunburst chart
    fig = px.sunburst(
        df_melted.dropna(subset=['TWh', 'Continent']),
        path=['Continent', 'Entity', 'Energy_Source'],
        values='TWh',
        color='Continent',
        title=f'Electricity Hierarchy (Top 3 per Continent) - {year}',
        height=700,
        color_discrete_sequence=px.colors.qualitative.Pastel
    )

    fig.update_layout(
        margin=dict(t=10, l=10, r=10, b=10),
        hoverlabel=dict(bgcolor="white", font_size=12),
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color="white")
    )
    return fig

def plot_global_energy_mix(df):
    # Aggregate global electricity production by source and year
    global_mix = df.groupby('Year')[[
        'Electricity from fossil fuels (TWh)',
        'Electricity from nuclear (TWh)',
        'Electricity from renewables (TWh)'
    ]].sum().reset_index()

    fig = go.Figure()
    COLORS = {
    "amber": "rgba(255, 184, 0, 1)",     # Fossil fuels
    "blue": "rgba(0, 210, 255, 1)",      # Nuclear
    "green": "rgba(0, 255, 65, 1)"       # Renewables
    }
    # Fossil fuels
    fig.add_trace(go.Scatter(
        x=global_mix['Year'], y=global_mix['Electricity from fossil fuels (TWh)'],
        mode='lines', line=dict(width=0.5, color=COLORS["amber"]),
        stackgroup='one', name='Fossil Fuels',
    fillcolor=COLORS["amber"].replace("1)", "0.6)")
    ))
    
    # Nuclear
    fig.add_trace(go.Scatter(
        x=global_mix['Year'], y=global_mix['Electricity from nuclear (TWh)'],
        mode='lines', line=dict(width=0.5, color=COLORS["blue"]),
        stackgroup='one', name='Nuclear',
        fillcolor=COLORS["blue"].replace("1)", "0.6)")
    ))
    
    # Renewables
    fig.add_trace(go.Scatter(
        x=global_mix['Year'], y=global_mix['Electricity from renewables (TWh)'],
        mode='lines', line=dict(width=0.5, color=COLORS["green"]),
        stackgroup='one', name='Renewables',
        fillcolor=COLORS["green"].replace("1)", "0.6)")
    ))

    fig.update_layout(
        height=400, margin=dict(t=10, b=10, l=10, r=10),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color="white"),
        xaxis=dict(gridcolor='rgba(255,255,255,0.1)', title="Year"),
        yaxis=dict(gridcolor='rgba(255,255,255,0.1)', title="TWh"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig
