from dash import Dash, html, dash_table, dcc, callback, Output, Input
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
pio.templates.default = "plotly_dark"
from plotly.subplots import make_subplots
import json
import seaborn as sns

pal = sns.color_palette("Dark2")

def make_scatter_plot(df):
    line_colors = [pal.as_hex()[0],
                   pal.as_hex()[1],
                   pal.as_hex()[2],
                   pal.as_hex()[3],
    ]
    # Get unique energy sources
    unique_energy_sources = df["energy_source_level_2"].unique()

    fig = make_subplots(rows=len(unique_energy_sources),
                        cols=1,
                        x_title="Total Energy by Sector (MWh)",
                        y_title="Sectoral Energy Contribution",
                        shared_yaxes='all')

    for j, i in enumerate(unique_energy_sources):
        fig.add_trace(go.Scatter(x=df[df["energy_source_level_2"] == i]["total_energy_by_sector(MWh)"],
                            y=df[df["energy_source_level_2"] == i]["relative_energy_proportion"],
                            name=i, mode="markers", marker_color=line_colors[j],
                            marker={
                                "sizemode": "area",
                                "size": df[df["energy_source_level_2"] == i]["count"],
                                "sizeref": max(df[df["energy_source_level_2"] == i]["count"])/300
                            },
                            customdata=df[df["energy_source_level_2"] == i]["kan_name"],
                            hovertemplate="<b>%{customdata}</b><br><br>" +
                            "Yearly energy production(MWh): %{x:.1f}<br>" + 
                            "Proportion of energy production: %{y:.1f}<br>" +
                            "No. energy facilities: %{marker.size:.1f}<br>" +
                            "<extra></extra>"),
                    row=j+1, col=1)
    fig.update_layout(
        title="",
        legend_itemsizing="constant",
        legend_title_text="Energy Sector",
        height=600,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    fig.update_xaxes(
        mirror=True,
        ticks='outside',
        showline=True
    )
    fig.update_yaxes(
        mirror=True,
        ticks='outside',
        showline=True
    )

    return fig

def make_pie_plot(df):
    pie_colors = [pal.as_hex()[0],
                  pal.as_hex()[1],
                  pal.as_hex()[2],
                  pal.as_hex()[3],
    ]
    
    fig = make_subplots(rows=1, cols=2,
                        specs=[[{"type": "pie"}, {"type": "pie"}]],
                        subplot_titles=("Yearly Production by Sector", "Number of Facilities by Sector"))
    
    fig.add_trace(go.Pie(labels=df["energy_source_level_2"],
                         values=df["total_energy_by_sector(MWh)"],
                         hole=.4,
                         sort=False,
                         textinfo="percent",
                         textposition="inside",
                         name="",
                         marker_colors=pie_colors),
    row=1, col=1)

    fig.add_trace(go.Pie(labels=df["energy_source_level_2"],
                         values=df["count"],
                         hole=.4,
                         sort=False,
                         textinfo="percent",
                         textposition="inside",
                         name="",
                         marker_colors=pie_colors),
    row=1, col=2),

    fig.update_layout(
        uniformtext_minsize=8,
        uniformtext_mode="hide"
    )

    return fig

def make_map_plot(df, geo_json, data_type='production'):
    """
    Create a map plot for renewable energy production or facilities in Switzerland.

    Args:
        df (DataFrame): DataFrame containing the energy data.
                        Should include 'yearly_production(MWh)' and columns for counting facilities.
        geo_json (dict): GeoJSON object for Switzerland.
        data_type (str): 'production' for total energy production (MWh) or
                         'facilities' for total number of energy facilities.

    Returns:
        fig (Figure): Plotly figure object.
    """
    if data_type == 'production':
        df_aggregated = df.groupby("kan_name")["yearly_production(MWh)"].agg("sum").reset_index(name="yearly_production(MWh)")
        color_column = "yearly_production(MWh)"
        color_scale = "Greens"
        hover_name = "Total Energy Production (MWh)"
        title_text = "Total Renewable Energy Production (MWh) per Canton"
    elif data_type == 'facilities':
        df_aggregated = df.groupby(['kan_name']).size().reset_index(name="total_facilities")
        color_column = "total_facilities"
        color_scale = "Oranges"
        hover_name = "Number of Energy Facilities"
        title_text = "Total Number of Renewable Energy Facilities per Canton"
    else:
        raise ValueError("Invalid data_type. Must be 'production' or 'facilities'.")
    
    custom_data_values = df_aggregated[['kan_name', color_column]].values.tolist()

    fig = go.Figure()

    fig.add_trace(
        go.Choroplethmap(
                geojson=geo_json,
                locations=df_aggregated['kan_name'],
                z=df_aggregated[color_column],
                featureidkey="properties.kan_name",
                colorscale=color_scale,
                marker={"line": {"width": 0.001, "color": "white"}},
                customdata=custom_data_values
            )
        )
    fig.update_layout( 
        map_style="carto-darkmatter",
        map_zoom=6, 
        map_center={"lat": 46.8, "lon": 8.2},
        title_text=title_text,
        title_x=0.5
        )
    fig.update_traces(
        hovertemplate="<b>%{customdata[0]}</b><br><br>" +
                f"{hover_name}: %{{customdata[1]:.0f}}<extra></extra>") 
    
    return fig

def create_sector_breakdown_chart(df_data, selected_canton, selected_data_type):

    if selected_canton == "All Cantons":
        # For 'facilities', you'd count the occurrences of each energy_source_level_2
        if selected_data_type == 'facilities':
            sector_data = df_data.groupby("energy_source_level_2").size().reset_index(name='facility_count')
            marker_color= pal.as_hex()[1]  # Orange for facilities
            title_text = "National Facilities by Sector"
        else: # 'production'
            sector_data = df_data.groupby("energy_source_level_2")["yearly_production(MWh)"].sum().reset_index()
            marker_color= pal.as_hex()[0]  # Green for production
            title_text = "National Energy by Sector"
    else:
        canton_df = df_data[df_data["kan_name"] == selected_canton]
        if selected_data_type == 'facilities':
            sector_data = canton_df.groupby("energy_source_level_2").size().reset_index(name='facility_count')
            marker_color= pal.as_hex()[1]
            title_text = f"Facilities by Sector in {selected_canton}"
        else: # 'production'
            sector_data = canton_df.groupby("energy_source_level_2")["yearly_production(MWh)"].sum().reset_index()
            marker_color= pal.as_hex()[0]
            title_text = f"Energy by Sector in {selected_canton}"

    # Determine the column to use for aggregation and the y-axis title
    if selected_data_type == 'production':
        y_column = "yearly_production(MWh)"
        y_axis_title = "Total Energy (MWh)"
    else:
        y_column = "facility_count"
        y_axis_title = "Number of Facilities"

    fig = go.Figure(data=[go.Bar(x=sector_data["energy_source_level_2"],
                                 y=sector_data[y_column], # Use the determined y_column
                                 marker_color=marker_color)])
    fig.update_layout(title=title_text,
                      xaxis_title="Energy Sector",
                      yaxis_title=y_axis_title) # Use the determined y-axis title
    return fig

def create_hist_facilities_by_year(df):

    facilities_by_year = df.groupby(["commissioning_year"]).size().reset_index(name= "facilities_by_year")

    fig = go.Figure()

    fig.add_trace(go.Bar(x=facilities_by_year["commissioning_year"],
                         y=facilities_by_year["facilities_by_year"],
                         name="Facilities by Year",
                         marker_color=pal.as_hex()[0]))
    fig.update_layout(
        title="Total Facilities",
        xaxis_title="Year",
        yaxis_title="Number of Facilities"
    )
    return fig

def create_facilities_by_sector(df):

    line_colors = [pal.as_hex()[0],
                   pal.as_hex()[1],
                   pal.as_hex()[2],
                   pal.as_hex()[3],
    ]
    facilities_per_sector_by_year = df.groupby(["commissioning_year", "energy_source_level_2"]).size().reset_index(
        name= "facilities_by_sector")
    unique_energy_sources = facilities_per_sector_by_year["energy_source_level_2"].unique()

    fig = make_subplots(rows=len(unique_energy_sources),
                        cols=1,
                        x_title="Year",
                        y_title="Number of Facilities",
                        shared_xaxes=True)
    for j, i in enumerate(unique_energy_sources):
        fig.add_trace(go.Scatter(x=facilities_per_sector_by_year[facilities_per_sector_by_year["energy_source_level_2"] == i]["commissioning_year"],
                                y=facilities_per_sector_by_year[facilities_per_sector_by_year["energy_source_level_2"] == i]["facilities_by_sector"],
                                mode="lines+markers",
                                marker_size=10,
                                line=dict(width=2),
                                name=i,
                                marker_color=line_colors[j]),
                    row=j+1, col=1)
    fig.update_layout(
        title="Sectoral Facilities",
        legend_itemsizing="constant",
        legend_title_text="Energy Sector",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    return fig