from dash import dcc, html, Input, Output, State, callback, ctx
from dash.exceptions import PreventUpdate
import dash
from dotenv import load_dotenv
from database import fetch_data_from_sql
import pandas as pd
from pandas.api.types import is_numeric_dtype
from dash_ag_grid import AgGrid

# Load environment variables
load_dotenv(override=True)

# ===== CONFIGURATION CONSTANTS =====

# Type detection
TYPE_DETECTION_SAMPLE_SIZE = 200
NUMERIC_THRESHOLD = 0.5

# Table definitions
CORE_TABLES = {
    "db_main": "Growth/Survival",
    "budburst_detailed_all": "All Budburst Stages",
    "biomass_destructive_2021": "Biomass",
    "leaf_traits_2016": "Leaf traits",
}

MATERNAL_TREE_TABLE = "Valley oak maternal tree climate data BCM 2018_03_08"
GARDENS_TABLE = "gardens_20152023prismmonthly"

# Whitelists for validation
ALLOWED_CORE_TABLES = set(CORE_TABLES.keys())

# Create a layout for the joins tab
joins_layout = dcc.Tab(
    label="Table Joins",
    id="joins-tab",
    style={"padding": "15px"},
    children=[
        dcc.Store(id='joins-tab-active', data=False),
        dcc.Store(id='join-tab-full-query', data=None),  # Store the SQL query instead of data
        dcc.Store(id='joins-metadata-store', data={}),  # Cache metadata (column lists)
        html.Div(
            [
                # Introduction section
                html.Div([
                    html.H4("Join Your Data", style={"marginBottom": "10px", "color": "#133817"}),
                    html.P(
                        "Automatically combines your garden dataset with maternal tree climate data and garden climate data. "
                        "All columns are selected by default. Please uncheck any you don't need.",
                        style={"color": "#666", "marginBottom": "20px", "fontSize": "0.95em"}
                    ),
                ], style={"marginBottom": "25px", "padding": "15px", "backgroundColor": "#f0f7f2", "borderRadius": "8px"}),

                # Step 1: Pick the core table
                html.Div([
                    html.H5("Step 1: Select Your Garden Dataset", style={"fontWeight": "bold", "marginBottom": "10px", "color": "#133817"}),
                    html.P("Choose the main dataset you want to work with:", style={"color": "#666", "marginBottom": "8px", "fontSize": "0.9em"}),
                    dcc.Dropdown(
                        id="join-tab-core-dropdown",
                        options=[{"label":value, "value":key} for key,value in CORE_TABLES.items()],
                        placeholder="Select a Garden Dataset..."
                    ),
                ], style={"marginBottom": "25px", "padding": "15px", "backgroundColor": "#ffffff", "borderRadius": "8px", "border": "1px solid #e0e0e0"}),

                # Error message for general errors
                html.Div(id="join-tab-general-error", style={"color": "red", "marginTop": "10px", "fontWeight": "bold", "textAlign": "center"}),

                # Step 2: Core table columns (in a card)
                html.Div([
                    html.Div([
                        html.H5("Garden Dataset Columns", style={"fontWeight": "bold", "marginBottom": "5px", "color": "#133817"}),
                        html.P("All columns are selected by default. Uncheck any you don't need.", 
                               style={"color": "#666", "fontSize": "0.85em", "marginBottom": "10px"}),
                        html.Div([
                            html.Button("Select All", id="join-select_all_btn", n_clicks=0, 
                                      style={"marginRight": "10px", "fontSize": "0.85em", "padding": "5px 12px", 
                                            "backgroundColor": "#007bff", "color": "white", "border": "none", "borderRadius": "4px", "cursor": "pointer"}),
                            html.Button("Deselect All", id="join-deselect_all_btn", n_clicks=0, 
                                      style={"fontSize": "0.85em", "padding": "5px 12px", 
                                            "backgroundColor": "#6c757d", "color": "white", "border": "none", "borderRadius": "4px", "cursor": "pointer"}),
                        ], style={"marginBottom": "10px"}),
                    ]),
                    dcc.Checklist(id="join-core-table-options", options=[], value=[], inline=False,
                                labelStyle={"display": "block", "marginBottom": "5px", "padding": "3px"},
                                style={"maxHeight": "250px", "overflowY": "auto", "padding": "10px", 
                                      "backgroundColor": "#f9f9f9", "borderRadius": "5px"}),
                ], id="join-table-columns-container", style={"display": "none", "marginBottom": "20px", 
                                                              "padding": "15px", "backgroundColor": "#ffffff", 
                                                              "borderRadius": "8px", "border": "1px solid #e0e0e0"}),

                # Step 3: Maternal tree table columns (in a card)
                html.Div([
                    html.Div([
                        html.H5("Maternal Tree Climate Data", style={"fontWeight": "bold", "marginBottom": "5px", "color": "#133817"}),
                        html.P("Climate data from the original tree locations. Automatically matched by Accession and Locality.", 
                               style={"color": "#666", "fontSize": "0.85em", "marginBottom": "10px"}),
                        html.Div([
                            html.Button("Select All", id="join-select_all_btn-2", n_clicks=0, 
                                      style={"marginRight": "10px", "fontSize": "0.85em", "padding": "5px 12px", 
                                            "backgroundColor": "#007bff", "color": "white", "border": "none", "borderRadius": "4px", "cursor": "pointer"}),
                            html.Button("Deselect All", id="join-deselect_all_btn-2", n_clicks=0, 
                                      style={"fontSize": "0.85em", "padding": "5px 12px", 
                                            "backgroundColor": "#6c757d", "color": "white", "border": "none", "borderRadius": "4px", "cursor": "pointer"}),
                        ], style={"marginBottom": "10px"}),
                    ]),
                    dcc.Checklist(id="join-tree-table-options", options=[], value=[], inline=False,
                                labelStyle={"display": "block", "marginBottom": "5px", "padding": "3px"},
                                style={"maxHeight": "250px", "overflowY": "auto", "padding": "10px", 
                                      "backgroundColor": "#f9f9f9", "borderRadius": "5px"}),
                ], id="join-tree-table-columns-container", style={"display": "none", "marginBottom": "20px",
                                                                    "padding": "15px", "backgroundColor": "#ffffff", 
                                                                    "borderRadius": "8px", "border": "1px solid #e0e0e0"}),

                # Step 4: Garden climate variables (in a card)
                html.Div([
                    html.Div([
                        html.H5("Garden Climate Data", style={"fontWeight": "bold", "marginBottom": "5px", "color": "#133817"}),
                        html.P("Monthly climate data from garden sites. Automatically matched by Site (and Year, if available).", 
                               style={"color": "#666", "fontSize": "0.85em", "marginBottom": "10px"}),
                        html.Div([
                            html.Button("Select All", id="join-select_all_btn-3", n_clicks=0, 
                                      style={"marginRight": "10px", "fontSize": "0.85em", "padding": "5px 12px", 
                                            "backgroundColor": "#007bff", "color": "white", "border": "none", "borderRadius": "4px", "cursor": "pointer"}),
                            html.Button("Deselect All", id="join-deselect_all_btn-3", n_clicks=0, 
                                      style={"fontSize": "0.85em", "padding": "5px 12px", 
                                            "backgroundColor": "#6c757d", "color": "white", "border": "none", "borderRadius": "4px", "cursor": "pointer"}),
                        ], style={"marginBottom": "10px"}),
                    ]),
                    dcc.Checklist(id="join-garden-table-options", options=[], value=[], inline=False,
                                labelStyle={"display": "block", "marginBottom": "5px", "padding": "3px"},
                                style={"maxHeight": "250px", "overflowY": "auto", "padding": "10px", 
                                      "backgroundColor": "#f9f9f9", "borderRadius": "5px"}),
                ], id="join-garden-table-columns-container", style={"display": "none", "marginBottom": "20px",
                                                                     "padding": "15px", "backgroundColor": "#ffffff", 
                                                                     "borderRadius": "8px", "border": "1px solid #e0e0e0"}),

                # Join preview section (shows before execution)
                html.Div([
                    html.H5("Join Preview", style={"fontWeight": "bold", "marginBottom": "10px", "color": "#133817"}),
                    html.Div(id="join-tab-preview", style={"padding": "10px", "backgroundColor": "#f8f9fa", 
                                                           "borderRadius": "5px", "color": "#666", "fontSize": "0.9em"}),
                ], id="join-tab-preview-container", style={"display": "none", "marginBottom": "20px",
                                                           "padding": "15px", "backgroundColor": "#ffffff", 
                                                           "borderRadius": "8px", "border": "1px solid #e0e0e0"}),

                # Execute button
                html.Div([
                    html.Button(
                        "Join Data & View Results",
                        id="join-tab-execute-button",
                        n_clicks=0,
                        style={
                            "backgroundColor": "#28a745",
                            "color": "white",
                            "border": "none",
                            "borderRadius": "6px",
                            "padding": "12px 30px",
                            "fontSize": "16px",
                            "fontWeight": "bold",
                            "cursor": "pointer",
                            "boxShadow": "0 2px 4px rgba(0,0,0,0.1)"
                        }
                    )
                ], id="join-tab-execute-button-div", style={"display": "none", "textAlign": "center", "marginTop": "20px", "marginBottom": "20px"}),

                # Row count input (similar to dataset.py) with debouncing
                html.Div([
                    html.Label("Number of rows to display:", style={"fontWeight": "bold"}),
                    dcc.Input(id="join-row-count", type="number", min=1, max=1000000, value=20,
                            style={"width": "100px", "margin": "10px 0"}, debounce=True),
                    html.Span(id="join-max-rows-info", style={"marginLeft": "10px", "color": "#666", "fontSize": "0.9em"}),
                ], id="join-row-count-container", style={"display": "none", "marginBottom": "15px"}),
                
                # Error message div
                html.Div([
                    html.Div([
                        html.Strong("⚠️ Please select at least one data source", style={"color": "#dc3545"}),
                        html.P("You need to select at least one column from either Maternal Tree Data or Garden Climate Data to proceed.", 
                               style={"color": "#666", "marginTop": "5px", "marginBottom": "0", "fontSize": "0.9em"})
                    ])
                ], id="join-tab-execute-error", style={"display": "none", "textAlign": "center", "marginTop": "20px",
                                                       "padding": "15px", "backgroundColor": "#fff3cd", 
                                                       "borderRadius": "8px", "border": "1px solid #ffc107"}),
                
                # Join execution div - only shows after successful execution
                html.Div(id="join-tab-results-div", style={"display": "none", "padding": "20px", "backgroundColor": "#ffffff", 
                                                     "borderRadius": "8px", "border": "1px solid #e0e0e0"}, children=[
                    html.H4("Results", style={"marginBottom": "15px", "color": "#133817"}),
                    
                    # Filter and selection counts
                    html.Div([
                        html.Span(id='join-filter-count-text', style={"marginRight": "20px", "fontWeight": "bold"}),
                        html.Span(id='join-selected-count-text', style={"fontWeight": "bold", "marginRight": "12px"}),
                    ], style={"marginBottom": "8px"}),
                    
                    # Loading indicator - wraps placeholder that gets replaced with grid
                    dcc.Loading(
                        id="join-grid-loading",
                        type="default",
                        children=html.Div(id="join-grid-wrapper", style={"maxHeight": "600px", "overflowY": "auto", "backgroundColor": "#e5ecf6", 
                                 "padding": "10px", "borderRadius": "5px", "border": "1px solid #d1d1d1", "marginBottom": "15px"})
                    ),
                    
                    # Stats and download section
                    html.Div([
                        html.Div(id="join-tab-results-stats", style={"marginTop": "15px", "color": "#666", "fontSize": "0.95em"}),
                        
                        # Download warning (for large datasets)
                        html.Div(id="join-download-warning", style={"marginTop": "10px"}),
                        
                        html.Div([
                            html.Div([
                                html.Label("Customize filename (optional):", style={"fontWeight": "bold", "marginBottom": "5px", "fontSize": "0.9em"}),
                                html.Div([
                                    dcc.Input(
                                        id="join-tab-csv-filename",
                                        type="text",
                                        placeholder="joined_data",
                                        value="joined_data",
                                        style={
                                            "padding": "8px 12px",
                                            "border": "1px solid #ccc",
                                            "borderRadius": "4px",
                                            "fontSize": "14px",
                                            "width": "250px",
                                            "marginRight": "10px"
                                        }
                                    ),
                                    html.Span(".csv", style={"fontSize": "14px", "color": "#666"})
                                ], style={"display": "flex", "alignItems": "center", "marginBottom": "15px"})
                            ], style={"marginTop": "15px", "marginBottom": "10px"}),
                            html.Div([
                                html.Button(
                                    "Download Filtered/Sorted Data (CSV)",
                                    id="download-join-tab-csv-button",
                                    style={
                                        "backgroundColor": "#007bff",
                                        "color": "white",
                                        "border": "none",
                                        "borderRadius": "4px",
                                        "padding": "8px 20px",
                                        "fontSize": "14px",
                                        "cursor": "pointer",
                                        "marginRight": "10px"
                                    }
                                ),
                                html.Button(
                                    "Download All Data (CSV)",
                                    id="download-join-tab-all-csv-button",
                                    style={
                                        "backgroundColor": "#28a745",
                                        "color": "white",
                                        "border": "none",
                                        "borderRadius": "4px",
                                        "padding": "8px 20px",
                                        "fontSize": "14px",
                                        "cursor": "pointer"
                                    }
                                ),
                            ], style={"display": "flex", "flexWrap": "wrap", "gap": "10px"}),
                        ]),
                        dcc.Download(id="download-join-tab-csv"),
                        dcc.Download(id="download-join-tab-all-csv")
                    ])
                ])
            ]
        )
    ]
) 



# ====== HELPERS ======

def validate_table_name(table_name, allowed_set):
    """Validate table name against whitelist."""
    if table_name not in allowed_set:
        raise ValueError(f"Invalid table name: {table_name}")
    return table_name

def apply_filter_model(df, filter_model):
    """Apply AG Grid filter model to a DataFrame"""
    for field, model in (filter_model or {}).items():
        if field not in df.columns:
            continue
        # Text filter
        if model.get('filterType') == 'text' or isinstance(df[field].dtype, object):
            fval = str(model.get('filter', ''))
            ftype = model.get('type', 'contains')
            if ftype == 'contains':
                df = df[df[field].astype(str).str.contains(fval, na=False, case=False)]
            elif ftype == 'equals':
                df = df[df[field].astype(str) == fval]
            elif ftype == 'notEqual':
                df = df[df[field].astype(str) != fval]
            elif ftype == 'startsWith':
                df = df[df[field].astype(str).str.startswith(fval, na=False)]
            elif ftype == 'endsWith':
                df = df[df[field].astype(str).str.endswith(fval, na=False)]
            else:
                # Default to contains
                df = df[df[field].astype(str).str.contains(fval, na=False, case=False)]
        else:
            # Numeric filter
            comp = model.get('type')
            val = model.get('filter')
            if val is None:
                continue
            val = float(val)
            if comp == 'lessThan':
                df = df[pd.to_numeric(df[field], errors='coerce') < val]
            elif comp == 'lessThanOrEqual':
                df = df[pd.to_numeric(df[field], errors='coerce') <= val]
            elif comp == 'greaterThan':
                df = df[pd.to_numeric(df[field], errors='coerce') > val]
            elif comp == 'greaterThanOrEqual':
                df = df[pd.to_numeric(df[field], errors='coerce') >= val]
            elif comp == 'equals':
                df = df[pd.to_numeric(df[field], errors='coerce') == val]
            elif comp == 'notEqual':
                df = df[pd.to_numeric(df[field], errors='coerce') != val]
    return df

def get_column_lists_cached(metadata_store):
    """Get cached column lists or fetch if not cached."""
    cache_key = "all_columns"
    
    if cache_key in metadata_store:
        return metadata_store[cache_key]
    
    # Fetch all column lists
    try:
        # Gardens table
        gardens_df = fetch_data_from_sql(f"SELECT TOP 1 * FROM dbo.[{GARDENS_TABLE}]")
        gardens_cols = gardens_df.columns.tolist() if gardens_df is not None else []
        
        # Maternal tree table
        tree_df = fetch_data_from_sql(f"SELECT TOP 1 * FROM dbo.[{MATERNAL_TREE_TABLE}]")
        tree_cols = tree_df.columns.tolist() if tree_df is not None else []
        
        return {
            'gardens_columns': gardens_cols,
            'tree_columns': tree_cols
        }
    except Exception as e:
        print(f"Error fetching column lists: {e}")
        return {
            'gardens_columns': [],
            'tree_columns': []
        }



# ====== CALLBACKS ======

# Track tab selection state
@callback(
    Output('joins-tab-active', 'data'),
    [Input('main-tabs', 'value')]  
)
def set_tab_active(tab_value):
    return tab_value == 'joins-tab'

# Reset all components when tab is switched
@callback(
    [Output('join-tab-core-dropdown', 'value', allow_duplicate=True),
     Output('join-core-table-options', 'options', allow_duplicate=True),
     Output('join-core-table-options', 'value', allow_duplicate=True),
     Output('join-tree-table-options', 'options', allow_duplicate=True),
     Output('join-tree-table-options', 'value', allow_duplicate=True),
     Output('join-garden-table-options', 'options', allow_duplicate=True),
     Output('join-garden-table-options', 'value', allow_duplicate=True),
     Output('join-table-columns-container', 'style', allow_duplicate=True),
     Output('join-tree-table-columns-container', 'style', allow_duplicate=True),
     Output('join-garden-table-columns-container', 'style', allow_duplicate=True),
     Output('join-tab-execute-button-div', 'style', allow_duplicate=True),
     Output('join-tab-execute-error', 'style', allow_duplicate=True),
     Output('join-tab-results-div', 'style', allow_duplicate=True),
     Output('join-tab-results-stats', 'children', allow_duplicate=True),
     Output('join-tab-preview-container', 'style', allow_duplicate=True),
     Output('join-tab-preview', 'children', allow_duplicate=True),
     Output('join-tab-full-query', 'data', allow_duplicate=True),
     Output('join-grid-wrapper', 'children', allow_duplicate=True),
     Output('join-tab-csv-filename', 'value', allow_duplicate=True),
     Output('join-row-count', 'value', allow_duplicate=True),
     Output('join-row-count-container', 'style', allow_duplicate=True),
     Output('join-tab-general-error', 'children', allow_duplicate=True)],
    [Input('joins-tab-active', 'data')],
    prevent_initial_call=True
)
def reset_tab_data(is_active):
    if is_active:
        raise PreventUpdate
    # Reset all controls when leaving the tab
    return (None, [], [], [], [], [], [], 
            {"display": "none"}, {"display": "none"}, {"display": "none"}, 
            {"display": "none"}, {"display": "none"}, {"display": "none"},
            "", {"display": "none"}, "", None, html.Div(), "joined_data", 20, {"display": "none"}, "")

# Cache metadata when tab becomes active
@callback(
    Output('joins-metadata-store', 'data'),
    [Input('joins-tab-active', 'data')],
    [State('joins-metadata-store', 'data')],
    prevent_initial_call=True
)
def cache_metadata_on_tab_active(is_active, metadata_store):
    if not is_active or 'all_columns' in metadata_store:
        raise PreventUpdate
    
    # Fetch and cache column lists
    column_data = get_column_lists_cached(metadata_store)
    metadata_store['all_columns'] = column_data
    return metadata_store

# Reset core table columns when core table changes
@callback(
    [Output('join-core-table-options', 'value', allow_duplicate=True),
     Output('join-tree-table-options', 'value', allow_duplicate=True),
     Output('join-garden-table-options', 'value', allow_duplicate=True),
     Output('join-tab-results-div', 'style', allow_duplicate=True),
     Output('join-tab-execute-error', 'style', allow_duplicate=True),
     Output('join-tab-preview-container', 'style', allow_duplicate=True),
     Output('join-row-count-container', 'style', allow_duplicate=True),
     Output('join-tab-general-error', 'children', allow_duplicate=True)],
    [Input('join-tab-core-dropdown', 'value')],
    prevent_initial_call=True
)
def reset_columns_on_table_change(selected_table):
    # Reset all column selections and hide results when core table changes
    return [], [], [], {"display": "none"}, {"display": "none"}, {"display": "none"}, {"display": "none"}, ""

# Handle conditionally rendered variable checklist - AUTO-SELECT ALL BY DEFAULT
@callback(
    [Output("join-core-table-options", "options"),
     Output("join-core-table-options", "value"),
     Output("join-table-columns-container", "style"),
     Output("join-tree-table-options", "options"),
     Output("join-tree-table-options", "value"),
     Output("join-tree-table-columns-container", "style"),
     Output("join-garden-table-options", "options"),
     Output("join-garden-table-options", "value"),
     Output("join-garden-table-columns-container", "style"),
     Output("join-tab-execute-button-div", "style"),
     Output("join-tab-preview-container", "style"),
     Output("join-row-count-container", "style"),
     Output("join-tab-general-error", "children")],
    [Input("join-tab-core-dropdown", "value")],
    [State('joins-metadata-store', 'data')]
)
def update_core_table_columns(selected_table, metadata_store):
    if selected_table is None:
        return [], [], {"display": "none"}, [], [], {"display": "none"}, [], [], {"display": "none"}, {"display": "none"}, {"display": "none"}, {"display": "none"}, ""

    try:
        # Validate table name
        validate_table_name(selected_table, ALLOWED_CORE_TABLES)
        
        # Get cached column data
        column_data = metadata_store.get('all_columns', {})
        
        if not column_data:
            column_data = get_column_lists_cached(metadata_store)
        
        # Get columns from cache
        gardens_cols = column_data.get('gardens_columns', [])
        tree_cols = column_data.get('tree_columns', [])
        
        # Create options
        GARDENS_TABLE_OPTIONS = [{'label': c, 'value': c} for c in gardens_cols]
        gardens_default_values = gardens_cols  # Auto-select all
        
        MATERNAL_TREE_OPTIONS = [{'label': c, 'value': c} for c in tree_cols]
        tree_default_values = tree_cols  # Auto-select all

        # Fetch core table columns (not cached since it depends on selection)
        sample_df = fetch_data_from_sql(f"SELECT TOP 1 * FROM [dbo].[{selected_table}]")
        if sample_df is None or sample_df.empty:
            error_msg = "Error: Could not fetch columns from selected table"
            return [], [], {"display": "none"}, [], [], {"display": "none"}, [], [], {"display": "none"}, {"display": "none"}, {"display": "none"}, {"display": "none"}, error_msg
        
        cols = sample_df.columns.tolist()
        opts = [{'label': c, 'value': c} for c in cols]
        core_default_values = cols  # Auto-select all
        
        return (opts, core_default_values, {"display": "block", "marginBottom": "20px", 
                                            "padding": "15px", "backgroundColor": "#ffffff", 
                                            "borderRadius": "8px", "border": "1px solid #e0e0e0"}, 
                MATERNAL_TREE_OPTIONS, tree_default_values, {"display": "block", "marginBottom": "20px",
                                                              "padding": "15px", "backgroundColor": "#ffffff", 
                                                              "borderRadius": "8px", "border": "1px solid #e0e0e0"}, 
                GARDENS_TABLE_OPTIONS, gardens_default_values, {"display": "block", "marginBottom": "20px",
                                                                  "padding": "15px", "backgroundColor": "#ffffff", 
                                                                  "borderRadius": "8px", "border": "1px solid #e0e0e0"}, 
                {"display": "block", "textAlign": "center", "marginTop": "20px", "marginBottom": "20px"},
                {"display": "block", "marginBottom": "20px", "padding": "15px", "backgroundColor": "#ffffff", 
                 "borderRadius": "8px", "border": "1px solid #e0e0e0"},
                {"display": "block", "marginBottom": "15px"},
                "")
    except ValueError as ve:
        error_msg = f"Security Error: {str(ve)}"
        print(error_msg)
        return [], [], {"display": "none"}, [], [], {"display": "none"}, [], [], {"display": "none"}, {"display": "none"}, {"display": "none"}, {"display": "none"}, error_msg
    except Exception as e:
        error_msg = f"Error fetching columns: {str(e)}"
        print(error_msg)
        return [], [], {"display": "none"}, [], [], {"display": "none"}, [], [], {"display": "none"}, {"display": "none"}, {"display": "none"}, {"display": "none"}, error_msg

# Handle Core table Select All and Deselect All buttons
@callback(
    Output('join-core-table-options', 'value', allow_duplicate=True),
    [Input('join-select_all_btn', 'n_clicks'), 
     Input('join-deselect_all_btn', 'n_clicks')],
    [State('join-core-table-options', 'options')],
    prevent_initial_call=True
)
def handle_core_select_buttons(select_all_clicks, deselect_all_clicks, current_options):
    trigger_id = ctx.triggered_id if ctx.triggered_id else None

    if trigger_id == 'join-select_all_btn' and current_options:
        return [opt['value'] for opt in current_options]
    if trigger_id == 'join-deselect_all_btn':
        return []
    
    raise PreventUpdate

# Handle Tree table Select All and Deselect All buttons
@callback(
    Output('join-tree-table-options', 'value', allow_duplicate=True),
    [Input('join-select_all_btn-2', 'n_clicks'), 
     Input('join-deselect_all_btn-2', 'n_clicks')],
    [State('join-tree-table-options', 'options')],
    prevent_initial_call=True
)
def handle_tree_select_buttons(select_all_clicks, deselect_all_clicks, current_options):
    trigger_id = ctx.triggered_id if ctx.triggered_id else None

    if trigger_id == 'join-select_all_btn-2' and current_options:
        return [opt['value'] for opt in current_options]
    if trigger_id == 'join-deselect_all_btn-2':
        return []
    
    raise PreventUpdate

# Handle Garden table Select All and Deselect All buttons
@callback(
    Output('join-garden-table-options', 'value', allow_duplicate=True),
    [Input('join-select_all_btn-3', 'n_clicks'), 
     Input('join-deselect_all_btn-3', 'n_clicks')],
    [State('join-garden-table-options', 'options')],
    prevent_initial_call=True
)
def handle_garden_select_buttons(select_all_clicks, deselect_all_clicks, current_options):
    trigger_id = ctx.triggered_id if ctx.triggered_id else None

    if trigger_id == 'join-select_all_btn-3' and current_options:
        return [opt['value'] for opt in current_options]
    if trigger_id == 'join-deselect_all_btn-3':
        return []
    
    raise PreventUpdate

# Update join preview based on selections
@callback(
    [Output("join-tab-preview", "children"),
     Output("join-tab-preview-container", "style", allow_duplicate=True)],
    [Input("join-tab-core-dropdown", "value"),
     Input("join-core-table-options", "value"),
     Input("join-tree-table-options", "value"),
     Input("join-garden-table-options", "value")],
    prevent_initial_call=True
)
def update_join_preview(core_table, core_vars, tree_vars, garden_vars):
    if not core_table:
        return "", {"display": "none"}
    
    preview_parts = []
    
    # Core table info
    core_name = CORE_TABLES.get(core_table, core_table)
    core_count = len(core_vars) if core_vars else 0
    preview_parts.append(html.Div([
        html.Strong(f"{core_name}:"), 
        html.Span(f" {core_count} columns selected", style={"marginLeft": "10px"})
    ], style={"marginBottom": "8px"}))
    
    # Maternal tree info
    if tree_vars:
        tree_count = len(tree_vars)
        preview_parts.append(html.Div([
            html.Strong("Maternal Tree Climate:"), 
            html.Span(f" {tree_count} columns selected", style={"marginLeft": "10px"}),
            html.Br(),
            html.Span("(Matched by Accession + Locality)", style={"fontSize": "0.85em", "color": "#888", "marginLeft": "20px"})
        ], style={"marginBottom": "8px"}))
    
    # Garden climate info
    if garden_vars:
        garden_count = len(garden_vars)
        if core_table == "leaf_traits_2016":
            match_info = "(Matched by Site)"
        else:
            match_info = "(Matched by Year + Site)"
        preview_parts.append(html.Div([
            html.Strong("Garden Climate:"), 
            html.Span(f" {garden_count} columns selected", style={"marginLeft": "10px"}),
            html.Br(),
            html.Span(match_info, style={"fontSize": "0.85em", "color": "#888", "marginLeft": "20px"})
        ], style={"marginBottom": "8px"}))
    
    if not tree_vars and not garden_vars:
        preview_parts.append(html.Div([
            html.Span("ERROR: Select at least one data source to combine", style={"color": "#ffc107", "fontStyle": "italic"})
        ]))
    
    return preview_parts, {"display": "block", "marginBottom": "20px", "padding": "15px", 
                          "backgroundColor": "#ffffff", "borderRadius": "8px", "border": "1px solid #e0e0e0"}

# Main execution callback - generates the SQL query (no count initially)
@callback(
    [
        Output("join-tab-full-query", "data"),
        Output("join-tab-csv-filename", "value", allow_duplicate=True),
        Output("join-tab-results-div", "style", allow_duplicate=True),
        Output("join-row-count-container", "style", allow_duplicate=True),
        Output("join-tab-execute-button", "children"),
        Output("join-tab-execute-button", "disabled"),
        Output("join-tab-general-error", "children", allow_duplicate=True),
        Output("join-row-count", "value"),
    ],
    [Input("join-tab-execute-button", "n_clicks")],
    [
        State("join-tab-core-dropdown", "value"),
        State("join-core-table-options", "value"),
        State("join-tree-table-options", "value"),
        State("join-garden-table-options", "value"),
    ],
    prevent_initial_call=True,
)
def execute_join(n_clicks, core_table, core_table_vars, maternal_tree_vars, garden_climate_vars):
    if not n_clicks or not core_table or (not maternal_tree_vars and not garden_climate_vars):
        raise PreventUpdate

    try:
        # Validate table name
        validate_table_name(core_table, ALLOWED_CORE_TABLES)
        
        # 1) Required core columns
        if core_table == "leaf_traits_2016":
            required_core_cols = ["Accession", "Locality", "Site"]
            garden_key_cols = {"Site"}
        else:
            required_core_cols = ["Accession", "Locality", "Year", "Site"]
            garden_key_cols = {"Year", "Site"}
        tree_key_cols = {"Accession", "Locality"}

        # 2) Core SELECT
        core_cols = required_core_cols[:]
        if core_table_vars:
            core_cols += [c for c in core_table_vars if c not in core_cols]
        core_sel = ", ".join(f"core.[{c}]" for c in core_cols)
        selected_clauses = [core_sel]

        # 3) Clean out any key‐columns from the non‐core selections
        safe_tree_vars   = [c for c in maternal_tree_vars   or [] if c not in tree_key_cols]
        safe_garden_vars = [c for c in garden_climate_vars or [] if c not in garden_key_cols]

        # 4) Maternal‐tree join
        joins = []
        if maternal_tree_vars:
            # only add non‐key columns to SELECT
            if safe_tree_vars:
                tree_sel = ", ".join(
                    f"maternal.[{c}] AS [maternal_{c.replace(' ', '_')}]"
                    for c in safe_tree_vars
                )
                selected_clauses.append(tree_sel)

            # build a subquery that SELECTs keys + only the safe vars
            tree_cols = ["TRY_CAST(TRY_CAST([Accession] AS NUMERIC) AS INT) AS [Accession]",
                         "[Locality]"] \
                        + [f"[{c}]" for c in safe_tree_vars]
            joins.append(f"""
LEFT JOIN (
  SELECT {', '.join(tree_cols)}
  FROM [dbo].[{MATERNAL_TREE_TABLE}]
) maternal
  ON core.[Accession] = maternal.[Accession]
 AND core.[Locality]  = maternal.[Locality]
""".strip())

        # 5) Garden‐climate join
        if garden_climate_vars:
            if safe_garden_vars:
                garden_sel = ", ".join(
                    f"garden.[{c}] AS [garden_{c.replace(' ', '_')}]"
                    for c in safe_garden_vars
                )
                selected_clauses.append(garden_sel)

            if core_table == "leaf_traits_2016":
                garden_cols = ["[Site]"] + [f"[{c}]" for c in safe_garden_vars]
                join_cond   = "core.[Site] = garden.[Site]"
            else:
                garden_cols = ["TRY_CAST(TRY_CAST([Year] AS NUMERIC) AS INT) AS [Year]",
                               "[Site]"] + [f"[{c}]" for c in safe_garden_vars]
                join_cond   = "core.[Year] = garden.[Year] AND core.[Site] = garden.[Site]"

            joins.append(f"""
LEFT JOIN (
  SELECT {', '.join(garden_cols)}
  FROM [dbo].[{GARDENS_TABLE}]
) garden
  ON {join_cond}
""".strip())

        # 6) Assemble base query (without TOP clause)
        base_query = f"""
SELECT DISTINCT
  {', '.join(selected_clauses)}
FROM [dbo].[{core_table}] core
{chr(10).join(joins)}
""".strip()
        
        # Generate default filename based on core table name
        default_filename = CORE_TABLES.get(core_table, "joined_data").lower().replace(" ", "_").replace("/", "_")
        
        # Store the base query (without TOP) - count will be determined after first query
        return (base_query, default_filename, 
                {"display": "block", "padding": "20px", "backgroundColor": "#ffffff", "borderRadius": "8px", "border": "1px solid #e0e0e0"}, 
                {"display": "block", "marginBottom": "15px"}, 
                "Join Data & View Results", False, "", 20)

    except ValueError as ve:
        error_msg = f"Security Error: {str(ve)}"
        print("Security error:", error_msg)
        return None, dash.no_update, {"display": "none"}, {"display": "none"}, "Join Data & View Results", False, error_msg, 20
    except Exception as e:
        error_msg = f"Error executing join: {str(e)}"
        print("SQL Error:", error_msg)
        return None, dash.no_update, {"display": "none"}, {"display": "none"}, "Join Data & View Results", False, error_msg, 20

# Update the grid data based on row count (and determine total count from actual query)
@callback(
    [Output('join-grid-wrapper', 'children'),
     Output('join-tab-results-stats', 'children'),
     Output('join-max-rows-info', 'children'),
     Output('join-row-count', 'max'),
     Output('download-join-tab-csv-button', 'children'),
     Output('download-join-tab-all-csv-button', 'children'),
     Output('join-download-warning', 'children'),
     Output('join-tab-results-div', 'style', allow_duplicate=True),
     Output('join-row-count-container', 'style', allow_duplicate=True)],
    [Input('join-tab-full-query', 'data'),
     Input('join-row-count', 'value')],
    prevent_initial_call=True
)

def update_grid_display(base_query, row_count):
    if not base_query or row_count is None:
        raise PreventUpdate

    try:
        # Validate row count
        if row_count < 1:
            row_count = 20

        # Execute a single query that returns BOTH the requested rows and the full result count
        # COUNT(*) OVER() computes the total rows in the subquery without needing a second COUNT(*) query.
        display_query = f"""
SELECT TOP {row_count}
  q.*,
  COUNT(*) OVER() AS __total_count__
FROM (
  {base_query}
) AS q
"""

        result_df = fetch_data_from_sql(display_query)

        if result_df is None or result_df.empty:
            empty_div = html.Div("No results returned", style={"padding": "20px", "textAlign": "center", "color": "#666"})
            return empty_div, "No results returned", "", 1000000, dash.no_update, dash.no_update, html.Div(), {"display": "block", "padding": "20px", "backgroundColor": "#ffffff", "borderRadius": "8px", "border": "1px solid #e0e0e0"}, {"display": "block", "marginBottom": "15px"}

        # Pull the total count and then drop the helper column so it doesn't show in the grid/downloads
        total_count = 0
        if "__total_count__" in result_df.columns:
            try:
                total_count = int(result_df["__total_count__"].iloc[0])
            except Exception:
                total_count = 0
            result_df = result_df.drop(columns=["__total_count__"], errors="ignore")

        actual_rows = len(result_df)

        # Max rows info (mirror dataset tab pattern)
        if total_count > 0:
            total_count_text = f"{total_count:,}"
            max_rows_text = f"(Max: {total_count:,} rows available)"
            max_val = total_count
        else:
            # Fallback: we couldn't determine total count; keep behavior permissive
            total_count_text = f"{actual_rows:,}+"
            max_rows_text = ""
            max_val = 1000000

        # Prepare data for AG Grid
        row_data = result_df.to_dict("records")
        column_defs = []
        
        # Add checkbox column pinned to left
        column_defs.append({
            'headerName': '',
            'field': '__select__',
            'checkboxSelection': True,
            'headerCheckboxSelection': True,
            'pinned': 'left',
            'width': 50,
            'sortable': False,
            'filter': False
        })
        
        # Add column definitions with appropriate filters
        for c in result_df.columns:
            col_series = result_df[c]
            is_num = False
            
            # Determine if column is numeric
            try:
                if is_numeric_dtype(col_series):
                    is_num = True
                else:
                    # Try coercing a small sample to detect numbers
                    sample = pd.to_numeric(col_series.dropna().head(TYPE_DETECTION_SAMPLE_SIZE), errors='coerce')
                    if len(sample) > 0 and sample.notna().sum() / float(len(sample)) >= NUMERIC_THRESHOLD:
                        is_num = True
            except Exception:
                is_num = False
            
            if is_num:
                col_def = {
                    'headerName': c,
                    'field': c,
                    'filter': 'agNumberColumnFilter',
                    'filterParams': {
                        'filterOptions': ['equals', 'notEqual', 'lessThan', 'lessThanOrEqual', 'greaterThan', 'greaterThanOrEqual'],
                        'suppressAndOrCondition': True
                    }
                }
            else:
                col_def = {
                    'headerName': c,
                    'field': c,
                    'filter': 'agTextColumnFilter',
                    'filterParams': {
                        'filterOptions': ['contains','notContains','equals','notEqual','startsWith','endsWith'],
                        'suppressAndOrCondition': True
                    }
                }
            
            column_defs.append(col_def)
        
        # Create the grid component
        grid_component = html.Div(
            AgGrid(
                id='join-tab-grid',
                rowData=row_data,
                columnDefs=column_defs,
                defaultColDef={
                    'filter': True,
                    'sortable': True,
                    'resizable': True,
                    'minWidth': 50,
                    'width': 120
                },
                dashGridOptions={'rowSelection': 'multiple', 'rowMultiSelectWithClick': True},
                selectedRows=[],
                className='ag-theme-alpine',
                style={'width': '100%', 'height': '500px'},
                enableEnterpriseModules=False,
            ),
            style={"overflowX": "auto", "width": "100%"}
        )
        
        # Stats text - removed per user request
        stats_text = ""
        
        # Button texts
        filtered_btn_text = f"Download Filtered Dataset"
        full_btn_text = f"Download All Data ({total_count_text} rows)"
        
        # Download warning for large datasets
        download_warning = html.Div()
        if actual_rows >= 100000:
            download_warning = html.Div([
                html.Span("⚠️ ", style={"fontSize": "18px"}),
                html.Span(f"Large dataset warning: Downloading all data may take significant time and resources ({actual_rows:,}+ rows).", 
                         style={"fontWeight": "bold"})
            ], style={
                "color": "#856404",
                "backgroundColor": "#fff3cd",
                "border": "1px solid #ffeaa7",
                "borderRadius": "4px",
                "padding": "12px",
                "marginBottom": "10px"
            })

        return grid_component, stats_text, max_rows_text, max_val, filtered_btn_text, full_btn_text, download_warning, {"display": "block", "padding": "20px", "backgroundColor": "#ffffff", "borderRadius": "8px", "border": "1px solid #e0e0e0"}, {"display": "block", "marginBottom": "15px"}

    except Exception as e:
        error_msg = f"Error updating grid display: {str(e)}"
        print(error_msg)
        error_div = html.Div(error_msg, style={"padding": "20px", "color": "red"})
        return error_div, "", "", 1000000, dash.no_update, dash.no_update, html.Div(), {"display": "none"}, {"display": "none"}

# Reset results when any selection changes
@callback(
    [Output("join-tab-results-div", "style", allow_duplicate=True),
     Output("join-row-count-container", "style", allow_duplicate=True)],
    [Input("join-core-table-options", "value"),
     Input("join-tree-table-options", "value"),
     Input("join-garden-table-options", "value")],
    prevent_initial_call=True
)
def reset_results_on_selection_change(core_vars, tree_vars, garden_vars):
    # Hide results whenever selections change
    return {"display": "none"}, {"display": "none"}

# Update filter and selection counts for AG Grid
@callback(
    [Output('join-filter-count-text', 'children'), 
     Output('join-selected-count-text', 'children')],
    [Input('join-tab-grid', 'rowData'), 
     Input('join-tab-grid', 'selectedRows'), 
     Input('join-tab-grid', 'filterModel')]
)
def update_join_table_counts(row_data, selected_rows, filter_model):
    """Update the filtered and selected row counts for AG Grid"""
    if not row_data:
        return "", ""
    
    df = pd.DataFrame(row_data)

    if filter_model:
        filtered = apply_filter_model(df, filter_model)
    else:
        filtered = df

    filtered_count = len(filtered)
    selected_count = len(selected_rows) if selected_rows else 0

    return f"Filtered rows: {filtered_count}", f"Selected rows: {selected_count}"

# Update download button text based on filtering
@callback(
    [Output("download-join-tab-csv-button", "children", allow_duplicate=True)],
    [Input('join-tab-grid', 'rowData'),
     Input('join-tab-grid', 'filterModel')],
    prevent_initial_call=True
)
def update_download_button_text(row_data, filter_model):
    """Update download button text based on current filter state"""
    if not row_data:
        raise PreventUpdate
    
    try:
        df = pd.DataFrame(row_data)
        
        if filter_model:
            filtered = apply_filter_model(df, filter_model)
            filtered_count = len(filtered)
        else:
            filtered_count = len(df)
        
        filtered_btn_text = f"Download Filtered Dataset ({filtered_count:,} rows)"
        
        return [filtered_btn_text]
    except Exception as e:
        print(f"Error updating download button: {e}")
        raise PreventUpdate

# Download filtered/sorted data from AG Grid
@callback(
    Output('download-join-tab-csv', 'data'),
    Input('download-join-tab-csv-button', 'n_clicks'),
    [State('join-tab-grid', 'rowData'),
     State('join-tab-grid', 'selectedRows'),
     State('join-tab-grid', 'filterModel'),
     State('join-tab-csv-filename', 'value')],
    prevent_initial_call=True
)
def download_filtered_join_results(n_clicks, row_data, selected_rows, filter_model, custom_filename):
    if not n_clicks or not row_data:
        raise PreventUpdate
    
    try:
        # Priority 1: Use selected rows if any
        if selected_rows and len(selected_rows) > 0:
            data_to_download = selected_rows
        # Priority 2: Use filtered data if filters are applied
        elif filter_model:
            df = pd.DataFrame(row_data)
            filtered_df = apply_filter_model(df, filter_model)
            data_to_download = filtered_df.to_dict('records')
        # Priority 3: Use all grid data
        else:
            data_to_download = row_data
        
        if not data_to_download:
            raise PreventUpdate
        
        # Convert data back to DataFrame
        df = pd.DataFrame(data_to_download)
        if df.empty:
            raise PreventUpdate
        
        # Determine filename
        if custom_filename and custom_filename.strip():
            clean_filename = "".join(c for c in custom_filename.strip() if c.isalnum() or c in (' ', '-', '_')).strip()
            if not clean_filename:
                clean_filename = "joined_data"
            filename = f"{clean_filename}.csv"
        else:
            filename = "joined_data.csv"
        
        return dcc.send_data_frame(df.to_csv, filename, index=False)
    except Exception as e:
        print(f"Error during filtered download: {e}")
        raise PreventUpdate

# Download all data (unfiltered) - fetches from database
@callback(
    Output('download-join-tab-all-csv', 'data'),
    Input('download-join-tab-all-csv-button', 'n_clicks'),
    [State('join-tab-full-query', 'data'),
     State('join-tab-csv-filename', 'value')],
    prevent_initial_call=True
)
def download_all_join_results(n_clicks, base_query, custom_filename):
    if not n_clicks or not base_query:
        raise PreventUpdate
    
    try:
        # Fetch all data from database using the stored query
        df = fetch_data_from_sql(base_query)
        
        if df is None or df.empty:
            raise PreventUpdate
        
        # Determine filename
        if custom_filename and custom_filename.strip():
            clean_filename = "".join(c for c in custom_filename.strip() if c.isalnum() or c in (' ', '-', '_')).strip()
            if not clean_filename:
                clean_filename = "joined_data_all"
            filename = f"{clean_filename}_all.csv"
        else:
            filename = "joined_data_all.csv"
        
        return dcc.send_data_frame(df.to_csv, filename, index=False)
    except Exception as e:
        print(f"Error during full download: {e}")
        raise PreventUpdate

# Error button
@callback(
    Output("join-tab-execute-error", "style"),
    [Input("join-tab-execute-button", "n_clicks")],
    [State("join-core-table-options", "value"),
     State("join-tree-table-options", "value"),
     State("join-garden-table-options", "value")],
    prevent_initial_call=True
)
def show_error_message(n_clicks, core_table_vars, maternal_tree_vars, garden_climate_vars):
    if n_clicks is None or n_clicks == 0:
        raise PreventUpdate
    
    # Show error message if no maternal tree or garden climate variables are selected
    if not maternal_tree_vars and not garden_climate_vars:
        return {"display": "block", "textAlign": "center", "marginTop": "20px",
                "padding": "15px", "backgroundColor": "#fff3cd", 
                "borderRadius": "8px", "border": "1px solid #ffc107"}
    
    return {"display": "none"}