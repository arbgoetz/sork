from dash import dcc, html, Input, Output, State, callback, ctx, ALL, MATCH, ClientsideFunction
import dash
from charts import create_database_Table
from dotenv import load_dotenv
from database import fetch_data_from_sql
import os
import pandas as pd
from pandas.api.types import is_numeric_dtype
import plotly.express as px

# Load environment variables
load_dotenv()

# Table Options
table_options = os.getenv("TABLE_OPTIONS").split(",")

# Layout for Dataset Tab
dataset_layout = dcc.Tab(
    label="Dataset",
    id="dataset-tab",
    style={"padding": "15px"},
    children=[
        # Store the tab's active state
        dcc.Store(id="dataset-tab-active", data=False),
        html.Br(),
        html.H4("Table Display", style={"marginBottom": "20px"}),
        html.Label("Select a table:", style={"fontWeight": "bold", "marginBottom": "5px", "fontSize": "16px"}),
        dcc.Dropdown(table_options, id="dataset_dropdown", placeholder="Table Options"),
        # Column checklist
        html.Div([
            html.Div([
                html.Label("Select columns to include:", style={"fontWeight": "bold", "marginBottom": "5px"}),
                html.Button("Select All", id="select_all_btn", n_clicks=0, style={"marginLeft": "10px", "fontSize": "0.8em"}),
                html.Button("Deselect All", id="deselect_all_btn", n_clicks=0, style={"marginLeft": "10px", "fontSize": "0.8em"}),
            ], style={"display": "flex", "alignItems": "center", "marginBottom": "5px"}),
            dcc.Checklist(id="options", options=[], value=[], inline=False,
                          labelStyle={"display": "block", "marginBottom": "3px"},
                          style={"maxHeight": "200px", "overflowY": "auto", "padding": "10px", "backgroundColor": "#f9f9f9", "borderRadius": "5px"}),
        ], id="columns_container", style={"display": "none", "marginBottom": "15px"}),
        # Row count input
        html.Div([
            html.Label("Number of rows to display:", style={"fontWeight": "bold"}),
            dcc.Input(id="row_count", type="number", min=1, max=1000, value=20,
                      style={"width": "100px", "margin": "10px 0"}),
            html.Span(id="max_rows_info", style={"marginLeft": "10px", "color": "#666", "fontSize": "0.9em"}),
        ], id="row_count_container", style={"display": "none"}),
        # Placeholder message
        html.Div(id="placeholder_message", children=[
            html.H4(
                "Select a table name, columns, and number of rows to construct the table",
                style={"textAlign": "center", "marginTop": "50px", "color": "#666"}
            )
        ]),
        # Data table
        html.Div(html.Div(id="dataset_container", style={"display": "none"}, children=[
            html.Div(dcc.Graph(id="dataset", style={"marginBottom": "10px"}),
                     style={"overflowX": "auto", "width": "100%"})
        ]), style={"maxHeight": "800px", "overflowY": "auto", "backgroundColor": "#e5ecf6", "padding": "10px", "borderRadius": "5px", "border": "1px solid #d1d1d1"}),
        
        # Variable selectors for plotting
        html.Div([
            html.Label("Select variables to plot selected rows:", style={"fontWeight": "bold", "marginBottom": "5px"}),
            html.Div([
                html.Div([
                    html.Label("X-axis:", style={"marginRight": "5px"}),
                    dcc.Dropdown(id="x_variable_dropdown", options=[], placeholder="Select X variable", style={"width": "100%"}),
                ], style={"width": "45%", "display": "inline-block", "marginRight": "5%"}),
                html.Div([
                    html.Label("Y-axis:", style={"marginRight": "5px"}),
                    dcc.Dropdown(id="y_variable_dropdown", options=[], placeholder="Select Y variable", style={"width": "100%"}),
                ], style={"width": "45%", "display": "inline-block"}),
            ], style={"display": "flex", "alignItems": "center"}),
        ], id="variable_selector", style={"display": "none", "marginBottom": "15px"}),
        
        # Graph type explanation
        html.Div([
            html.Label("Graph types based on variable selection:", style={"fontWeight": "bold", "marginBottom": "5px"}),
            html.Ul([
                html.Li("Numerical + Numerical → Scatter plot"),
                html.Li("Numerical + Categorical → Bar chart (mean of numerical by category)"),
                html.Li("Categorical + Numerical → Bar chart (mean of numerical by category)"),
                html.Li("Categorical + Categorical → Bar chart and Heatmap"),
            ], style={"marginLeft": "20px", "fontSize": "0.9em"})
        ], id="graph_type_explanation", style={"display": "none", "marginBottom": "15px", "backgroundColor": "#f9f9f9", "padding": "10px", "borderRadius": "5px"}),
        
        # Generate figure button
        html.Div(html.Button("Generate Figure", id="generate_btn", n_clicks=0, disabled=True),
                 id="generate_button_div", style={"display": "none", "textAlign": "center", "marginBottom": "15px"}),
        # Figure output
        html.Div(id="figure_div", style={"display": "none"}, children=[
            dcc.Loading(dcc.Graph(id="figure_graph"), type="default")
        ]),
        # Footer spacer
        html.Div(style={"height": "50px", "backgroundColor": "#e5ecf6", "width": "100%", "marginTop": "10px", "borderTop": "1px solid #d1d1d1", "borderRadius": "0 0 5px 5px"})
    ]
)

# Callbacks

# Track tab selection state
@callback(
    Output('dataset-tab-active', 'data'),
    [Input('main-tabs', 'value')]  
)
def set_tab_active(tab_value):
    return tab_value == 'dataset-tab'

# Reset all components when tab is switched or table is changed
@callback(
    [Output('dataset_dropdown', 'value', allow_duplicate=True),
     Output('options', 'options', allow_duplicate=True),
     Output('options', 'value', allow_duplicate=True),
     Output('row_count', 'value', allow_duplicate=True),
     Output('x_variable_dropdown', 'value', allow_duplicate=True),
     Output('y_variable_dropdown', 'value', allow_duplicate=True),
     Output('figure_div', 'children', allow_duplicate=True), 
     Output('figure_div', 'style', allow_duplicate=True),
     Output('generate_btn', 'n_clicks', allow_duplicate=True)],
    [Input('dataset-tab-active', 'data')],
    prevent_initial_call=True
)
def reset_tab_data(is_active):
    if not is_active:
        # Reset all controls when leaving the tab
        return None, [], [], 20, None, None, [], {"display": "none"}, 0
    else:
        # Don't reset when entering the tab
        return [dash.no_update] * 9

# Handle table and column selection
@callback(
    [Output('options', 'options', allow_duplicate=True), 
     Output('options', 'value', allow_duplicate=True), 
     Output('columns_container', 'style')],
    [Input('dataset_dropdown', 'value')],
    prevent_initial_call=True
)
def update_column_options_on_table_change(selected_table):
    if selected_table is None:
        return [], [], {"display": "none"}
    try:
        sample_df = fetch_data_from_sql(f"SELECT TOP 1 * FROM [dbo].[{selected_table}]")
        cols = sample_df.columns.tolist()
        opts = [{'label': c, 'value': c} for c in cols]
        return opts, cols, {"display": "block", "marginBottom": "15px"}
    except Exception as e:
        print(f"Error fetching columns: {e}")
        return [], [], {"display": "none"}

# Reset dependent components when table changes
@callback(
    [Output('x_variable_dropdown', 'value', allow_duplicate=True), 
     Output('y_variable_dropdown', 'value', allow_duplicate=True),
     Output('figure_div', 'children', allow_duplicate=True), 
     Output('figure_div', 'style', allow_duplicate=True)],
    [Input('dataset_dropdown', 'value')],
    prevent_initial_call=True
)
def reset_dependent_components(selected_table):
    # Reset all dependent components when table changes
    return None, None, [], {"display": "none"}

# Handle Select All and Deselect All buttons
@callback(
    Output('options', 'value', allow_duplicate=True),
    [Input('select_all_btn', 'n_clicks'), 
     Input('deselect_all_btn', 'n_clicks')],
    [State('options', 'options'), State('options', 'value')],
    prevent_initial_call=True
)
def handle_select_buttons(select_all_clicks, deselect_all_clicks, current_options, current_values):
    trigger_id = ctx.triggered_id if ctx.triggered_id else 'no_trigger'
    
    if trigger_id == 'select_all_btn' and current_options:
        return [opt['value'] for opt in current_options]
    if trigger_id == 'deselect_all_btn':
        return []
    
    return dash.no_update

@callback(
    [Output('x_variable_dropdown', 'options'), Output('y_variable_dropdown', 'options')],
    Input('options', 'options')
)
def update_variable_dropdown_options(column_options):
    return column_options, column_options

@callback(
    [Output('max_rows_info', 'children'), Output('row_count', 'max')],
    Input('dataset_dropdown', 'value')
)
def update_row_count_info(selected_table):
    if selected_table is None:
        return "", 1000
    try:
        count_df = fetch_data_from_sql(f"SELECT COUNT(*) AS row_count FROM [dbo].[{selected_table}]")
        total = count_df.iloc[0]['row_count']
        return f"(Max: {total} rows available)", total
    except Exception as e:
        print(f"Error fetching row count: {e}")
        return "", 1000

@callback(
    [Output('dataset', 'figure'), Output('row_count_container', 'style'),
     Output('placeholder_message', 'style'), Output('dataset_container', 'style'),
     Output('variable_selector', 'style'), Output('generate_button_div', 'style'),
     Output('graph_type_explanation', 'style')],
    [Input('dataset_dropdown', 'value'), Input('options', 'value'), Input('row_count', 'value')],
    State('options', 'options')
)
def update_output(selected_table, selected_columns, row_count, column_options):
    no_display = {"display": "none"}
    if selected_table is None:
        return {}, no_display, {"display": "block"}, no_display, no_display, no_display, no_display
    if not selected_columns:
        cols = [opt['value'] for opt in column_options]
    else:
        cols = selected_columns
    if row_count is None:
        row_count = 20
    try:
        cnt_df = fetch_data_from_sql(f"SELECT COUNT(*) AS row_count FROM [dbo].[{selected_table}]")
        total = cnt_df.iloc[0]['row_count']
        row_count = min(row_count, total)
    except:
        pass
    table_index = table_options.index(selected_table)
    fig_table = create_database_Table(table_index, cols, row_count)
    return fig_table, {"display": "block", "margin": "10px 0"}, {"display": "none"}, {"display": "block"}, {"display": "block", "marginBottom": "15px"}, {"display": "block"}, {"display": "block", "marginBottom": "15px"}

@callback(
    Output('generate_btn', 'disabled'),
    Input('x_variable_dropdown', 'value'), Input('y_variable_dropdown', 'value')
)
def toggle_generate_button(x_var, y_var):
    return not (x_var and y_var)

@callback(
    [Output('figure_div', 'children', allow_duplicate=True), 
     Output('figure_div', 'style', allow_duplicate=True)],
    Input('generate_btn', 'n_clicks'),
    State('dataset_dropdown', 'value'),
    State('x_variable_dropdown', 'value'),
    State('y_variable_dropdown', 'value'),
    State('row_count', 'value'),
    prevent_initial_call=True
)
def generate_figure(n_clicks, selected_table, x_var, y_var, row_count):
    if not n_clicks or n_clicks == 0 or selected_table is None or x_var is None or y_var is None:
        return [], {"display": "none"}
    
    col1, col2 = x_var, y_var
    query = f"SELECT TOP {row_count} [{col1}], [{col2}] FROM [dbo].[{selected_table}]"
    df = fetch_data_from_sql(query)[[col1, col2]].dropna()
    num1, num2 = is_numeric_dtype(df[col1]), is_numeric_dtype(df[col2])
    
    if num1 and num2:
        fig = px.scatter(df, x=col1, y=col2, title=f"{col1} vs {col2}")
        graph = dcc.Graph(figure=fig)
        return graph, {"display": "block"}
    if num1 and not num2:
        num, cat = col1, col2
    elif num2 and not num1:
        num, cat = col2, col1
    else:
        num = cat = None
    
    if num and cat:
        df_agg = df.groupby(cat)[num].mean().reset_index()
        fig = px.bar(df_agg, x=cat, y=num, title=f"Mean {num} by {cat}")
        graph = dcc.Graph(figure=fig)
        return graph, {"display": "block"}
    
    fig_bar = px.bar(df, x=col1, color=col2, barmode='group', title=f"{col1} by {col2}")
    fig_heat = px.density_heatmap(df, x=col1, y=col2, title=f"Heatmap of {col1} vs {col2}")
    graph1 = dcc.Graph(figure=fig_bar)
    graph2 = dcc.Graph(figure=fig_heat)
    return [graph1, graph2], {"display": "block"}