import os
from dash import dcc, html, Input, Output, State, callback, dash_table, ctx
import dash
from dotenv import load_dotenv
from database import fetch_data_from_sql
import pandas as pd


# Load environment variables
load_dotenv()

table_options = os.getenv("TABLE_OPTIONS").split(',')

# Create a layout for the joins tab
joins_layout = dcc.Tab(
    label="Table Joins",
    id="joins-tab",
    style={"padding": "15px"},
    children=[
        # Store the tab's active state
        dcc.Store(id="joins-tab-active", data=False),
        html.Br(),
        html.H4("Table Joins", style={"marginBottom": "20px"}),
        
        # Main container for the join operation
        html.Div([
            # Left side - Join configuration
            html.Div([
                # First table selection
                html.Div([
                    html.Label("Step 1: Select first table", style={"fontWeight": "bold", "marginBottom": "5px"}),
                    dcc.Dropdown(
                        id="first-table-dropdown",
                        options=[{"label": table, "value": table} for table in table_options],
                        placeholder="Select first table"
                    ),
                ], style={"marginBottom": "15px"}),
                
                # Join type selection
                html.Div([
                    html.Label("Step 2: Select join type", style={"fontWeight": "bold", "marginBottom": "5px"}),
                    dcc.Dropdown(
                        id="join-type-dropdown",
                        options=[
                            {"label": "Inner Join", "value": "inner"},
                            {"label": "Left Join", "value": "left"},
                            {"label": "Right Join", "value": "right"},
                            {"label": "Full Outer Join", "value": "full"},
                        ],
                        placeholder="Select join type"
                    ),
                    html.Div([
                        html.Img(src="https://i.imgur.com/1sxnQ4j.png", style={"width": "100%", "marginTop": "10px"}),
                        html.P("Join visualization", style={"textAlign": "center", "color": "#666", "fontSize": "0.8em"})
                    ], id="join-visualization", style={"display": "none", "marginTop": "10px"})
                ], style={"marginBottom": "15px"}),
                
                # Second table selection
                html.Div([
                    html.Label("Step 3: Select second table", style={"fontWeight": "bold", "marginBottom": "5px"}),
                    dcc.Dropdown(
                        id="second-table-dropdown",
                        options=[{"label": table, "value": table} for table in table_options],
                        placeholder="Select second table"
                    ),
                ], style={"marginBottom": "15px"}),
                
                # Join key selection
                html.Div([
                    html.Label("Step 4: Select join keys", style={"fontWeight": "bold", "marginBottom": "5px"}),
                    html.Div([
                        html.Div([
                            html.Label("Key in first table:", style={"marginBottom": "5px"}),
                            dcc.Dropdown(id="first-table-key", placeholder="Select column")
                        ], style={"width": "48%"}),
                        html.Div([
                            html.Label("Key in second table:", style={"marginBottom": "5px"}),
                            dcc.Dropdown(id="second-table-key", placeholder="Select column")
                        ], style={"width": "48%"}),
                    ], style={"display": "flex", "justifyContent": "space-between"}),
                ], id="join-keys-div", style={"display": "none", "marginBottom": "15px"}),
                
                # Column selection
                html.Div([
                    html.Label("Step 5: Select columns to include", style={"fontWeight": "bold", "marginBottom": "5px"}),
                    html.Div([
                        html.Div([
                            html.Label("First table columns:", style={"marginBottom": "5px"}),
                            html.Button("Select All", id="first-table-select-all", n_clicks=0, 
                                       style={"marginLeft": "10px", "fontSize": "0.8em"}),
                            html.Button("Deselect All", id="first-table-deselect-all", n_clicks=0, 
                                       style={"marginLeft": "10px", "fontSize": "0.8em"})
                        ], style={"display": "flex", "alignItems": "center", "marginBottom": "5px"}),
                        dcc.Checklist(
                            id="first-table-columns",
                            options=[],
                            value=[],
                            style={"maxHeight": "150px", "overflowY": "auto", "padding": "10px", 
                                  "backgroundColor": "#f9f9f9", "borderRadius": "5px"}
                        )
                    ], style={"marginBottom": "10px"}),
                    html.Div([
                        html.Div([
                            html.Label("Second table columns:", style={"marginBottom": "5px"}),
                            html.Button("Select All", id="second-table-select-all", n_clicks=0, 
                                       style={"marginLeft": "10px", "fontSize": "0.8em"}),
                            html.Button("Deselect All", id="second-table-deselect-all", n_clicks=0, 
                                       style={"marginLeft": "10px", "fontSize": "0.8em"})
                        ], style={"display": "flex", "alignItems": "center", "marginBottom": "5px"}),
                        dcc.Checklist(
                            id="second-table-columns",
                            options=[],
                            value=[],
                            style={"maxHeight": "150px", "overflowY": "auto", "padding": "10px", 
                                  "backgroundColor": "#f9f9f9", "borderRadius": "5px"}
                        )
                    ])
                ], id="column-selection-div", style={"display": "none", "marginBottom": "15px"}),
                
                # Row limit
                html.Div([
                    html.Label("Step 6: Set row limit", style={"fontWeight": "bold", "marginBottom": "5px"}),
                    dcc.Input(
                        id="row-limit-input",
                        type="number",
                        min=1,
                        max=10000,
                        value=1000,
                        style={"width": "100px"}
                    ),
                ], id="row-limit-div", style={"display": "none", "marginBottom": "15px"}),
                
                # Execute join button
                html.Div([
                    html.Button(
                        "Execute Join",
                        id="execute-join-button",
                        style={
                            "backgroundColor": "#007bff",
                            "color": "white",
                            "border": "none",
                            "borderRadius": "4px",
                            "padding": "10px 20px",
                            "fontSize": "16px",
                            "cursor": "pointer"
                        }
                    )
                ], id="execute-button-div", style={"display": "none", "textAlign": "center", "marginTop": "20px"})
            ], style={"width": "40%", "padding": "20px", "backgroundColor": "#e5ecf6", "borderRadius": "10px"}),
            
            # Right side - Results
            html.Div([
                html.Div([
                    html.H5("Join Preview", style={"marginBottom": "15px"}),
                    html.Div(id="join-sql-query", style={"fontFamily": "monospace", "backgroundColor": "#f8f9fa", 
                                                          "padding": "10px", "borderRadius": "5px", 
                                                          "marginBottom": "15px", "overflowX": "auto"}),
                    dcc.Loading(
                        html.Div(id="join-results-table"),
                        type="circle"
                    ),
                    html.Div([
                        html.Div(id="join-results-stats", style={"marginTop": "15px", "color": "#666"}),
                        html.Button(
                            "Download CSV",
                            id="download-join-csv-button",
                            style={
                                "backgroundColor": "#28a745",
                                "color": "white",
                                "border": "none",
                                "borderRadius": "4px",
                                "padding": "5px 15px",
                                "marginTop": "15px"
                            }
                        ),
                        dcc.Download(id="download-join-csv")
                    ])
                ], id="join-results-div", style={"display": "none"})
            ], style={"width": "55%", "marginLeft": "5%", "padding": "20px", "backgroundColor": "#f0f2f5", 
                      "borderRadius": "10px", "maxHeight": "800px", "overflowY": "auto"})
        ], style={"display": "flex", "justifyContent": "space-between", "marginTop": "20px"}),
        
        # Placeholder message
        html.Div(
            html.H5("Select tables and join parameters to start", 
                   style={"textAlign": "center", "marginTop": "50px", "color": "#666"}),
            id="joins-placeholder"
        ),
        
        # Error message area
        html.Div(id="join-error-message", style={"color": "red", "marginTop": "20px", "fontWeight": "bold"})
    ]
)

# Track tab selection state
@callback(
    Output('joins-tab-active', 'data'),
    [Input('tabs', 'value')]
)
def set_joins_tab_active(tab_value):
    return tab_value == 'joins-tab'

# Reset when tab is switched
@callback(
    [Output('first-table-dropdown', 'value', allow_duplicate=True),
     Output('join-type-dropdown', 'value', allow_duplicate=True),
     Output('second-table-dropdown', 'value', allow_duplicate=True),
     Output('first-table-key', 'value', allow_duplicate=True),
     Output('second-table-key', 'value', allow_duplicate=True),
     Output('first-table-columns', 'options', allow_duplicate=True),
     Output('first-table-columns', 'value', allow_duplicate=True),
     Output('second-table-columns', 'options', allow_duplicate=True),
     Output('second-table-columns', 'value', allow_duplicate=True),
     Output('row-limit-input', 'value', allow_duplicate=True),
     Output('join-results-div', 'style', allow_duplicate=True),
     Output('joins-placeholder', 'style', allow_duplicate=True),
     Output('join-error-message', 'children', allow_duplicate=True)],
    [Input('joins-tab-active', 'data')],
    prevent_initial_call=True
)
def reset_joins_tab_data(is_active):
    if not is_active:
        # Reset all controls when leaving the tab
        return (None, None, None, None, None, 
                [], [], [], [], 1000, 
                {"display": "none"}, {"display": "block"}, "")
    else:
        # Don't reset when entering the tab
        return [dash.no_update] * 13

# Update the join visualization based on join type
@callback(
    [Output('join-visualization', 'style'),
     Output('join-visualization', 'children')],
    [Input('join-type-dropdown', 'value')]
)
def update_join_visualization(join_type):
    if not join_type:
        return {"display": "none"}, []
    
    # Image URLs for different join types
    join_images = {
        "inner": "/assets/inner.png",
        "left": "/assets/left.png",
        "right": "/assets/right.png",
        "full": "/assets/outer.png"
    }
    
    # Join type descriptions
    join_descriptions = {
        "inner": "Returns rows when there is a match in both tables",
        "left": "Returns all rows from the left table, and matched rows from the right table",
        "right": "Returns all rows from the right table, and matched rows from the left table",
        "full": "Returns all rows when there is a match in either table"
    }
    
    return {"display": "block", "marginTop": "10px"}, [
        html.Img(src=join_images[join_type], style={"width": "100%", "marginTop": "10px"}),
        html.P(join_descriptions[join_type], style={"textAlign": "center", "color": "#666", "fontSize": "0.9em"})
    ]

# Get columns for both tables when selected
@callback(
    [Output('join-keys-div', 'style'),
     Output('column-selection-div', 'style'),
     Output('row-limit-div', 'style'),
     Output('execute-button-div', 'style'),
     Output('first-table-key', 'options'),
     Output('second-table-key', 'options'),
     Output('first-table-columns', 'options'),
     Output('second-table-columns', 'options')],
    [Input('first-table-dropdown', 'value'),
     Input('second-table-dropdown', 'value'),
     Input('join-type-dropdown', 'value')]
)
def update_column_options(first_table, second_table, join_type):
    # Don't display anything if any selection is missing
    if not first_table or not second_table or not join_type:
        return {"display": "none"}, {"display": "none"}, {"display": "none"}, {"display": "none"}, [], [], [], []
    
    # Get columns from both tables
    try:
        first_df = fetch_data_from_sql(f"SELECT TOP 1 * FROM [dbo].[{first_table}]")
        second_df = fetch_data_from_sql(f"SELECT TOP 1 * FROM [dbo].[{second_table}]")
        
        first_columns = first_df.columns.tolist()
        second_columns = second_df.columns.tolist()
        
        first_column_options = [{"label": col, "value": col} for col in first_columns]
        second_column_options = [{"label": col, "value": col} for col in second_columns]
        
        # Show all divs
        return ({"display": "block", "marginBottom": "15px"}, 
                {"display": "block", "marginBottom": "15px"},
                {"display": "block", "marginBottom": "15px"},
                {"display": "block", "textAlign": "center", "marginTop": "20px"},
                first_column_options,
                second_column_options,
                first_column_options,
                second_column_options)
    except Exception as e:
        print(f"Error getting columns: {e}")
        return {"display": "none"}, {"display": "none"}, {"display": "none"}, {"display": "none"}, [], [], [], []

# Handle column selection buttons
@callback(
    Output('first-table-columns', 'value'),
    [Input('first-table-select-all', 'n_clicks'),
     Input('first-table-deselect-all', 'n_clicks')],
    [State('first-table-columns', 'options'), 
     State('first-table-columns', 'value')]
)
def handle_first_table_column_selection(select_clicks, deselect_clicks, options, current_value):
    trigger_id = ctx.triggered_id if ctx.triggered_id else 'no-id'
    
    if trigger_id == 'first-table-select-all':
        return [option['value'] for option in options]
    elif trigger_id == 'first-table-deselect-all':
        return []
    
    return current_value

@callback(
    Output('second-table-columns', 'value'),
    [Input('second-table-select-all', 'n_clicks'),
     Input('second-table-deselect-all', 'n_clicks')],
    [State('second-table-columns', 'options'), 
     State('second-table-columns', 'value')]
)
def handle_second_table_column_selection(select_clicks, deselect_clicks, options, current_value):
    trigger_id = ctx.triggered_id if ctx.triggered_id else 'no-id'
    
    if trigger_id == 'second-table-select-all':
        return [option['value'] for option in options]
    elif trigger_id == 'second-table-deselect-all':
        return []
    
    return current_value

# Generate and execute the join
@callback(
    [Output('join-results-div', 'style'),
     Output('joins-placeholder', 'style'),
     Output('join-sql-query', 'children'),
     Output('join-results-table', 'children'),
     Output('join-results-stats', 'children'),
     Output('join-error-message', 'children')],
    [Input('execute-join-button', 'n_clicks')],
    [State('first-table-dropdown', 'value'),
     State('join-type-dropdown', 'value'),
     State('second-table-dropdown', 'value'),
     State('first-table-key', 'value'),
     State('second-table-key', 'value'),
     State('first-table-columns', 'value'),
     State('second-table-columns', 'value'),
     State('row-limit-input', 'value')]
)
def execute_join(n_clicks, first_table, join_type, second_table, first_key, second_key, 
                 first_columns, second_columns, row_limit):
    if n_clicks is None or n_clicks == 0:
        return {"display": "none"}, {"display": "block"}, "", None, "", ""
    
    # Validate inputs
    if not first_table or not join_type or not second_table or not first_key or not second_key:
        return {"display": "none"}, {"display": "block"}, "", None, "", "Please select all required fields"
    
    if not first_columns and not second_columns:
        return {"display": "none"}, {"display": "block"}, "", None, "", "Please select at least one column from either table"
    
    try:
        # Format column selections for SQL query
        first_cols = []
        if first_columns:
            for col in first_columns:
                if col != first_key:  # Avoid duplicate keys in the result
                    first_cols.append(f"t1.[{col}] AS [t1_{col}]")
                else:
                    first_cols.append(f"t1.[{col}]")  # Don't rename the join key
        
        second_cols = []
        if second_columns:
            for col in second_columns:
                if col != second_key or col == first_key:  # Avoid duplicate keys or columns with same name
                    second_cols.append(f"t2.[{col}] AS [t2_{col}]")
                else:
                    second_cols.append(f"t2.[{col}]")
        
        # Construct the SQL query
        columns = ", ".join(first_cols + second_cols)
        if not columns.strip():
            columns = "t1.[" + first_key + "], t2.[" + second_key + "]"
        
        sql_query = f"""
        SELECT TOP {row_limit} {columns}
        FROM [dbo].[{first_table}] AS t1
        {join_type.upper()} JOIN [dbo].[{second_table}] AS t2
        ON t1.[{first_key}] = t2.[{second_key}]
        """
        
        # Execute the query
        result_df = fetch_data_from_sql(sql_query)
        
        # Create stats information
        row_count = len(result_df)
        stats_text = f"Showing {row_count} rows"
        if row_count == row_limit:
            stats_text += f" (limited to {row_limit} rows)"
        stats_text += f" | {len(result_df.columns)} columns"
        
        # Create the table display
        table = dash_table.DataTable(
            data=result_df.head(1000).to_dict('records'),
            columns=[{'name': col, 'id': col} for col in result_df.columns],
            page_size=15,
            style_table={'overflowX': 'auto'},
            style_cell={
                'minWidth': '100px',
                'maxWidth': '300px',
                'overflow': 'hidden',
                'textOverflow': 'ellipsis'
            },
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': 'rgb(248, 248, 248)'
                }
            ],
            filter_action="native",
            sort_action="native"
        )
        
        # Format the SQL query for display
        formatted_query = html.Pre(sql_query, style={"margin": 0})
        
        return {"display": "block"}, {"display": "none"}, formatted_query, table, stats_text, ""
    
    except Exception as e:
        error_message = str(e)
        return {"display": "none"}, {"display": "block"}, "", None, "", f"Error executing join: {error_message}"

# Download the join results as CSV
@callback(
    Output('download-join-csv', 'data'),
    [Input('download-join-csv-button', 'n_clicks')],
    [State('first-table-dropdown', 'value'),
     State('join-type-dropdown', 'value'),
     State('second-table-dropdown', 'value'),
     State('first-table-key', 'value'),
     State('second-table-key', 'value'),
     State('first-table-columns', 'value'),
     State('second-table-columns', 'value'),
     State('row-limit-input', 'value')]
)
def download_join_results(n_clicks, first_table, join_type, second_table, first_key, second_key, 
                         first_columns, second_columns, row_limit):
    if n_clicks is None or n_clicks == 0:
        return dash.no_update
    
    try:
        # Format column selections for SQL query
        first_cols = []
        if first_columns:
            for col in first_columns:
                if col != first_key:  # Avoid duplicate keys in the result
                    first_cols.append(f"t1.[{col}] AS [t1_{col}]")
                else:
                    first_cols.append(f"t1.[{col}]")  # Don't rename the join key
        
        second_cols = []
        if second_columns:
            for col in second_columns:
                if col != second_key or col == first_key:  # Avoid duplicate keys or columns with same name
                    second_cols.append(f"t2.[{col}] AS [t2_{col}]")
                else:
                    second_cols.append(f"t2.[{col}]")
        
        # Construct the SQL query
        columns = ", ".join(first_cols + second_cols)
        if not columns.strip():
            columns = "t1.[" + first_key + "], t2.[" + second_key + "]"
        
        sql_query = f"""
        SELECT TOP {row_limit} {columns}
        FROM [dbo].[{first_table}] AS t1
        {join_type.upper()} JOIN [dbo].[{second_table}] AS t2
        ON t1.[{first_key}] = t2.[{second_key}]
        """
        
        # Execute the query
        result_df = fetch_data_from_sql(sql_query)
        
        # Generate a filename based on the tables being joined
        filename = f"{first_table}_{join_type}_join_{second_table}.csv"
        
        return dcc.send_data_frame(result_df.to_csv, filename, index=False)
    except Exception as e:
        # If there's an error, don't download anything
        print(f"Error during download: {e}")
        return dash.no_update