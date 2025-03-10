from dash import dcc, html, Input, Output, callback, State, ctx
from charts import create_database_Table
from dotenv import load_dotenv
from database import fetch_data_from_sql
import os

# Load environment variables
load_dotenv()

# Table Options
table_options = os.getenv("TABLE_OPTIONS", "").split(",")

dataset_layout = dcc.Tab(
    [
        html.Br(),
        html.Label("Select a table:", style={"fontWeight": "bold", "marginBottom": "5px", "fontSize": "16px"}), 
        dcc.Dropdown(table_options, id="dataset_dropdown", placeholder="Table Options"),
        html.Div([
            html.Div([
                html.Label("Select columns to include:", style={"fontWeight": "bold", "marginBottom": "5px"}),
                html.Button("Select All", id="select_all_btn", n_clicks=0, 
                           style={"marginLeft": "10px", "fontSize": "0.8em"}),
                html.Button("Deselect All", id="deselect_all_btn", n_clicks=0, 
                           style={"marginLeft": "10px", "fontSize": "0.8em"}),
            ], style={"display": "flex", "alignItems": "center", "marginBottom": "5px"}),
            html.Div(
                dcc.Checklist(
                    id="options",
                    options=[],
                    value=[],
                    inline=False,
                    labelStyle={"display": "block", "marginBottom": "3px"},
                    style={"maxHeight": "200px", "overflowY": "auto", "padding": "10px", "backgroundColor": "#f9f9f9", "borderRadius": "5px"}
                ),
            ),
        ], id="columns_container", style={"display": "none", "marginBottom": "15px"}),  # Initially hidden
        html.Div([
            html.Label("Number of rows to display:", style={"fontWeight": "bold"}),
            dcc.Input(
                id="row_count",
                type="number",
                min=1,
                max=1000,  # This will be dynamically updated
                value=20,  # Default value
                style={"width": "100px", "margin": "10px 0"}
            ),
            html.Span(id="max_rows_info", style={"marginLeft": "10px", "color": "#666", "fontSize": "0.9em"}),
        ], id="row_count_container", style={"display": "none"}),  # Initially hidden
        html.Div(id="placeholder_message", children=[
            html.Div(
                html.H4("Select a table name, columns, and number of rows to construct the table", 
                        style={"textAlign": "center", "marginTop": "50px", "color": "#666"})
            )
        ]),
        # Wrap the dataset container in a fixed-height container with proper styling
        html.Div(
            html.Div(id="dataset_container", style={"display": "none"}, children=[
                # Create a div wrapper for the graph with horizontal scrolling if needed
                html.Div(
                    dcc.Graph(id="dataset", style={"marginBottom": "10px"}),
                    style={"overflowX": "auto", "width": "100%"}  # Enable horizontal scrolling
                ),
            ]),
            style={
                "maxHeight": "800px", 
                "overflowY": "auto", 
                "backgroundColor": "#e5ecf6", 
                "padding": "10px", 
                "borderRadius": "5px",
                "border": "1px solid #d1d1d1",
                "marginBottom": "0px"  # Remove bottom margin
            }
        ),
        # Add a proper footer that extends the full width
        html.Div(
            style={
                "height": "50px", 
                "backgroundColor": "#e5ecf6", 
                "width": "100%", 
                "marginTop": "10px",
                "borderTop": "1px solid #d1d1d1",
                "borderRadius": "0 0 5px 5px"
            }
        )
    ],
    label = "Dataset",
    style={"padding": "15px"}
)

@callback(
    [Output('options', 'options'),   # Populate column selection checklist
     Output('options', 'value'),     # Set default values (initially all selected)
     Output('columns_container', 'style')],  # Show/hide the column container
    [Input('dataset_dropdown', 'value'),
     Input('select_all_btn', 'n_clicks'),
     Input('deselect_all_btn', 'n_clicks')],
    [State('options', 'options'),
     State('options', 'value')]
)
def update_column_options(selected_table, select_all_clicks, deselect_all_clicks, current_options, current_values):
    """Fetches column names dynamically based on selected table and handles select/deselect actions."""
    # Identify which input triggered the callback
    trigger_id = ctx.triggered_id if ctx.triggered_id else 'no_trigger'
    
    # Handle Select All button
    if trigger_id == 'select_all_btn' and current_options:
        return current_options, [opt['value'] for opt in current_options], {"display": "block", "marginBottom": "15px"}
    
    # Handle Deselect All button
    if trigger_id == 'deselect_all_btn' and current_options:
        return current_options, [], {"display": "block", "marginBottom": "15px"}
    
    # Handle table selection change
    if trigger_id == 'dataset_dropdown' or trigger_id == 'no_trigger':
        if selected_table is None:
            return [], [], {"display": "none"}

        try:
            db_df = fetch_data_from_sql(f"SELECT TOP 1 * FROM [dbo].[{selected_table}]")  # Fetch sample row
            columns = db_df.columns.tolist()
            options = [{'label': col, 'value': col} for col in columns]
            # Initially select all columns
            default_values = columns
            return options, default_values, {"display": "block", "marginBottom": "15px"}
        except Exception as e:
            print(f"Error fetching columns for table {selected_table}: {e}")
            return [], [], {"display": "none"}
    
    # Default return for other cases
    return current_options, current_values, {"display": "block", "marginBottom": "15px"}

@callback(
    [Output('max_rows_info', 'children'),
     Output('row_count', 'max')],
    [Input('dataset_dropdown', 'value')]
)
def update_row_count_info(selected_table):
    if selected_table is None:
        return "", 1000

    # Get the total row count for this table
    try:
        count_query = f"SELECT COUNT(*) AS row_count FROM [dbo].[{selected_table}]"
        count_df = fetch_data_from_sql(count_query)
        total_rows = count_df.iloc[0]['row_count']
        return f"(Max: {total_rows} rows available)", total_rows
    except Exception as e:
        print(f"Error getting row count for table {selected_table}: {e}")
        return "(Unable to determine maximum rows)", 1000

@callback(
    [Output('dataset', 'figure'),
     Output('row_count_container', 'style'),
     Output('placeholder_message', 'style'),
     Output('dataset_container', 'style')],
    [Input('dataset_dropdown', 'value'),
     Input('options', 'value'),
     Input('row_count', 'value')],
    [State('options', 'options')]  # Add state to preserve options
)
def update_output(selected_table, selected_columns, row_count, column_options):
    # Set default styles
    row_count_style = {"display": "none"}
    placeholder_style = {"display": "block"}
    dataset_style = {"display": "none"}
    
    if selected_table is None:
        return {}, row_count_style, placeholder_style, dataset_style

    # Show row count selector when table is selected
    row_count_style = {"display": "block", "margin": "10px 0"}
    placeholder_style = {"display": "none"}
    dataset_style = {"display": "block"}
    
    # Default row count if not specified
    if row_count is None:
        row_count = 20
    
    # Get the total row count for this table
    try:
        count_query = f"SELECT COUNT(*) AS row_count FROM [dbo].[{selected_table}]"
        count_df = fetch_data_from_sql(count_query)
        total_rows = count_df.iloc[0]['row_count']
        # Ensure row_count doesn't exceed max
        if row_count > total_rows:
            row_count = total_rows
    except Exception as e:
        print(f"Error getting row count for table {selected_table}: {e}")
    
    # Handle selected columns
    if selected_columns is None or len(selected_columns) == 0:
        # If no columns selected and options are available, use all columns
        if column_options and len(column_options) > 0:
            selected_columns = [option['value'] for option in column_options]
        else:
            selected_columns = []

    table_index = table_options.index(selected_table)
    return create_database_Table(table_index, selected_columns, row_count), row_count_style, placeholder_style, dataset_style