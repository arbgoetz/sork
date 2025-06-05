import dash
from dash import dcc, html, Input, Output, callback, callback_context, dash_table
import plotly.graph_objects as go
import pandas as pd
from dotenv import load_dotenv
import os
from database import fetch_data_from_sql

# Load environment variables
load_dotenv(override=True)
map_table = os.getenv("MAP_TABLE")

map_layout = dcc.Tab(
    id="maps-tab",
    value="map-tab",
    children=[
        html.Br(),
        html.H4("Maternal Tree Locations", style={"marginBottom": "20px"}),
        
        html.Div([
            html.Div([
                # Header for the map
                html.Div([
                    html.Button("Reset View", id="reset-map", 
                               style={
                                   "backgroundColor": "#e9ebe8",
                                   "color": "white",
                                   "border": "1px solid #133817",
                                   "borderRadius": "4px",
                                   "padding": "5px 10px",
                                   "marginRight": "10px"
                               }),
                ], style={"marginBottom": "15px"}),
                
                # To track the click data 
                dcc.Store(id='stored-click-data', data=None),

                # The map itself
                dcc.Graph(
                    id='california-map',
                    style={'height': '70vh'},
                    config={
                        'scrollZoom': True,
                        'displayModeBar': True,
                        # Removed lasso tool since it's confusing to use
                        'modeBarButtonsToRemove': ['lasso2d']
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
                        "• Click the camera icon on the top right to download the plot",
                        html.Br(),
                    ], style={"fontSize": "0.9em", "color": "#666"})
                ], style={"marginTop": "15px"})
            ], className="col-12")
        ], className="row"),

        # Section for displaying the trees at each tree site
        html.Br(),
        html.Div([
            html.P("Click on a tree site to see details about the trees at that location.", 
                   style={"fontSize": "0.9em", "color": "#666"}),
        ], style={"marginTop": "15px", "width": "100%"}, id='individual-tree-data'),
    ],
    label="Tree Sites",
    style={"padding": "15px"}
)

# Callback to handle both map updates and click data
@callback(
    [Output('california-map', 'figure'),
     Output('stored-click-data', 'data')],
    [Input('reset-map', 'n_clicks'),
     Input('california-map', 'clickData')]
)
def update_map_and_click_data(reset_clicks, clickData):
    # Determine which input triggered the callback
    ctx = callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None
    
    # Create the base map figure
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
    ))
    
    # Set up the map layout
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
    
    # Handle click data - if the map was clicked, update the stored click data
    if trigger_id == 'california-map':
        return fig, clickData
    
    # If reset button was clicked or initial load, return the figure with no click data
    return fig, None

# Display information about the clicked tree site
@callback(
    Output('individual-tree-data', 'children'),
    [Input('stored-click-data', 'data')]
)
def display_click_data(clickData):
    if clickData and 'points' in clickData and len(clickData['points']) > 0:
        try:
            # Get the locality name from click data
            locality_name = clickData['points'][0]['text']
            
            # get column names from the table
            columns = fetch_data_from_sql(f"SELECT TOP 1 * FROM dbo.[{map_table}]").columns.tolist()
            columns.remove('Accession')
            columns_string = ', '.join(columns)

            # Fetch all data for this location
            df = fetch_data_from_sql(f"SELECT {columns_string} FROM dbo.[{map_table}] WHERE locality_full_name = '{locality_name}'")

            if df.empty:
                return html.Div([
                    html.H5(f"No data available for {locality_name}", style={"marginBottom": "10px", "color": "#dc3545"})
                ])
            
            # Create a nice layout for the data
            return html.Div([
                # Header with location name
                html.H5(f"Trees at {locality_name}", style={
                    "marginBottom": "15px", 
                    "backgroundColor": "#72b7eb", 
                    "color": "white",
                    "padding": "10px",
                    "borderRadius": "5px"
                }),
                
                # Display number of trees found
                html.P(f"Found {len(df)} trees at this location", style={"fontWeight": "bold", "marginBottom": "15px"}),
                
                # Data table with all information
                dash_table.DataTable(
                    id='tree-data-table',
                    columns=[{"name": col, "id": col} for col in df.columns],
                    data=df.to_dict('records'),
                    style_table={
                        'overflowX': 'auto',
                        'width': '100%',
                    },
                    style_cell={
                        'textAlign': 'left',
                        'padding': '8px',
                        'whiteSpace': 'normal',
                        'height': 'auto',
                    },
                    style_header={
                        'backgroundColor': '#f8f9fa',
                        'fontWeight': 'bold',
                        'borderBottom': '2px solid #dee2e6'
                    },
                    style_data_conditional=[
                        {
                            'if': {'row_index': 'odd'},
                            'backgroundColor': '#f2f2f2'
                        }
                    ],
                    page_size=10,  # Pagination to handle large datasets
                ),
            ])
        except Exception as e:
            # Handle any errors that might occur
            return html.Div([
                html.H5("Error retrieving data", style={"color": "#dc3545"}),
                html.P(f"An error occurred: {str(e)}")
            ])
    
    # Default message when no location is selected
    return html.P("Click on a tree site to see details about the trees at that location.", 
                 style={"fontSize": "0.9em", "color": "#666"})