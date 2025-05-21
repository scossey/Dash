from dash import Dash, html, dcc, callback, Output, Input
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
pio.templates.default = "plotly_dark"
from plotly.subplots import make_subplots
from process_energy_ch import create_df_for_plots, map_kanton_name
from energy_ch_figs import make_map_plot, create_sector_breakdown_chart, make_scatter_plot, create_hist_facilities_by_year, create_facilities_by_sector
import json

# Incorporate data
df = pd.read_csv('renewable_power_plants_CH_2020.csv')
df = map_kanton_name(df)

with open("georef-switzerland-kanton.geojson", "r") as file:
    ch = json.load(file)

concat = create_df_for_plots(df)

# Generate static figures
histogram_figure = create_hist_facilities_by_year(df)
ficilities_figure = create_facilities_by_sector(df)
scatter_figure = make_scatter_plot(concat)

# Initialize the app - incorporate css
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = Dash(external_stylesheets=external_stylesheets)
server = app.server

# App layout
app.layout = html.Div(
    style={'backgroundColor': 'black', 'color': 'white'},
    children=[
        html.Div(className='row', children='Renewable Energy Production in Switzerland',
                 style={'textAlign': 'center', 'fontSize': 30, 'padding': '20px 0'}),

        # Row for controls
        html.Div(className='row', children=[
            html.Div(className='eight columns', children=[
                html.Label('Select Map Data:'),
                dcc.RadioItems(
                    id='map-data-selector',
                    options=[
                        {'label': 'Total Production (MWh)', 'value': 'production'},
                        {'label': 'Number of Facilities', 'value': 'facilities'}],
                    value='production',
                    inline=True,
                    style={'color': 'white'})]),
            html.Div(className='four columns', children=[
                html.Label('Select Canton:'),
                dcc.Dropdown(
                    id='canton-dropdown',
                    options=[{'label': 'All Cantons', 'value': 'All Cantons'}] +
                            [{'label': c, 'value': c} for c in df['kan_name'].unique()],
                    value='All Cantons')])], # Default
                    style={'padding': '10px'}),

        # Row for the map plot
        html.Div(className='row', children=[
        # Map will take 8 columns (adjust as needed, total columns in a row must sum to 12 or less)
        html.Div(className='eight columns', children=[
            dcc.Graph(id='choropleth-map')]),

        # Sector breakdown chart will take 4 columns
        html.Div(className='four columns', children=[
            dcc.Graph(id='sector-breakdown-chart')])]),

        # Row for text    
        html.Div(className='row', children='Renewable Energy Facilities Commissioned by Year',
                 style={'textAlign': 'left', 'fontSize': 20, 'padding': '20px 0'}),

        # Row for the line plot and histogram
        html.Div(className='row', children=[
            html.Div(className='four columns', children=[
                dcc.Graph(id='histogram', figure=histogram_figure)]),

            html.Div(className='eight columns', children=[
                dcc.Graph(id='pie-plot', figure=ficilities_figure)])]),

        # Row for text    
        html.Div(className='row', children='Sectoral Energy Production by Canton',
                 style={'textAlign': 'left', 'fontSize': 20, 'padding': '20px 0'}),

        # Row for the scatter plot
        html.Div(className='row', children=[
            html.Div(className='eight columns', children=[
                dcc.Graph(id='scatter-plot', figure=scatter_figure)])])
        ])

# Define the callback to update the choropleth map
@app.callback(
    Output('choropleth-map', 'figure'), # Output to the figure property of the choropleth map
    Input('map-data-selector', 'value') # Input from the value of the radio items
)
def update_choropleth_map(selected_data_type):
    return make_map_plot(df, ch, selected_data_type)

# Updates the Canton-specific Energy Assessment
@app.callback(
    Output('sector-breakdown-chart', 'figure'),
    Input('canton-dropdown', 'value'), # update the chart based on the selected canton
    Input('map-data-selector', 'value') # update the chart based on the selected data type
)
def update_sector_chart(selected_canton, selected_data_type):
    return create_sector_breakdown_chart(df, selected_canton, selected_data_type)

if __name__ == '__main__':
    app.run(debug=True)