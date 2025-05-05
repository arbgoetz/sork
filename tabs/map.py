import dash
from dash import dcc, html, Input, Output, callback
import plotly.graph_objects as go
from dotenv import load_dotenv
import os
from database import fetch_data_from_sql

# Load environment variables
load_dotenv()

map_table = os.getenv("MAP_TABLE")

# Create a layout for the map tab
map_layout = dcc.Tab(
    [
        html.Br(),
        html.H4("California Map", style={"marginBottom": "20px"}),
        
        html.Div([
            html.Div([
                # Map controls (simplified)
                html.Div([
                    html.Button("Reset View", id="reset-map", 
                               style={
                                   "backgroundColor": "#6c757d",
                                   "color": "white",
                                   "border": "none",
                                   "borderRadius": "4px",
                                   "padding": "5px 10px",
                                   "marginRight": "10px"
                               }),
                ], style={"marginBottom": "15px"}),
                
                # The map itself
                dcc.Graph(
                    id='california-map',
                    style={'height': '70vh'},
                    config={
                        'scrollZoom': True,
                        'displayModeBar': True,
                        # Removed lasso and selection tools
                        'modeBarButtonsToRemove': ['lasso2d', 'select2d']
                    }
                ),
                
                # Simplified instructions
                html.Div([
                    html.P([
                        html.Strong("Map Navigation:"),
                        html.Br(),
                        "• Use the mouse wheel or pinch gesture to zoom in/out",
                        html.Br(),
                        "• Click and drag to pan the map",
                        html.Br(),
                        "• Click 'Reset View' to return to the default view of California",
                        html.Br(),
                        "• Click the camera icon on the top right to take download the plot",
                        html.Br(),
                    ], style={"fontSize": "0.9em", "color": "#666"})
                ], style={"marginTop": "15px"})
            ], className="col-12")
        ], className="row")
    ],
    label="California Map",
    style={"padding": "15px"}
)

# Callback to update the map based on user interactions
@callback(
    Output('california-map', 'figure'),
    [Input('reset-map', 'n_clicks')]
)
def update_map(reset_clicks):
    # Create the base map
    fig = go.Figure()

    # Fetch coordinates for map
    lon_list = fetch_data_from_sql(f"SELECT AVG(Longitude) AS avg_longitude FROM dbo.[{map_table}] GROUP BY locality_full_name")['avg_longitude'].tolist()
    lat_list = fetch_data_from_sql(f"SELECT AVG(Latitude) AS avg_latitude FROM dbo.[{map_table}] GROUP BY locality_full_name")['avg_latitude'].tolist()      
    text_list = fetch_data_from_sql(f"SELECT DISTINCT locality_full_name FROM dbo.[{map_table}]")['locality_full_name'].tolist()
    
    fig.add_trace(go.Scattermapbox(
        mode = "markers+text",
        lon = lon_list,
        lat = lat_list,
        text = text_list,
        textposition = "top right",
        marker = {'size':8, 'color':'#007bff'},
        hoverinfo='text'
    )),
    
    # Set up the map layout - using only standard map style
    # Always start with the zoomed-in view
    fig.update_layout(
        mapbox={
            'style': 'open-street-map',  
            'center': {'lon': -119.5, 'lat': 37.5},  # Center of California
            'zoom': 5  # Default zoomed in view
        },
        margin={'l': 0, 'r': 0, 't': 0, 'b': 0},
        height=600,
        paper_bgcolor="#e5ecf6",
        plot_bgcolor="#e5ecf6"
    )
    
    return fig