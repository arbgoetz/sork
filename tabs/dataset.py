from dash import dcc, html, Input, Output, State, callback, ctx
from dash.exceptions import PreventUpdate
import dash
from dotenv import load_dotenv
from database import fetch_data_from_sql
import os
import pandas as pd
from pandas.api.types import is_numeric_dtype
import plotly.express as px
from dash_ag_grid import AgGrid

# Load environment variables
load_dotenv(override=True)

# Table Options - Hardcoded whitelist
table_options = os.getenv("TABLE_OPTIONS").split(",")
ALLOWED_TABLES = set(table_options)

# Constants for type detection
TYPE_DETECTION_SAMPLE_SIZE = 200
NUMERIC_THRESHOLD = 0.5  # 50% of values must be numeric to classify as numeric

# Layout for Dataset Tab
dataset_layout = dcc.Tab(
    label="Tables",
    id="dataset-tab",
    style={"padding": "15px"},
    children=[
        # Store the tab's active state
        dcc.Store(id="dataset-tab-active", data=False),
        
        # Store for table metadata (row counts, column types)
        dcc.Store(id="table-metadata-store", data={}),

        # Main Header and Dropdown
        html.Br(),
        html.H4("Table View and Figure Generation", style={"marginBottom": "20px"}),
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
        
        # Row count input with debounce
        html.Div([
            html.Label("Number of rows to display:", style={"fontWeight": "bold"}),
            dcc.Input(id="row_count", type="number", min=1, max=1000, value=20,
                    style={"width": "100px", "margin": "10px 0"}, debounce=True),
            html.Span(id="max_rows_info", style={"marginLeft": "10px", "color": "#666", "fontSize": "0.9em"}),
        ], id="row_count_container", style={"display": "none"}),
        
        # Placeholder message
        html.Div(id="placeholder_message", children=[
            html.H5(
                "Select a table name, columns, and number of rows to construct the table",
                style={"textAlign": "center", "marginTop": "50px", "color": "#666"}
            ),
        ]),
        
        # Error message area
        html.Div(id="dataset-error-message", style={"color": "red", "marginTop": "20px", "fontWeight": "bold", "textAlign": "center"}),
        
        # Ag-Grid table display
        html.Div(id="dataset_container", style={"display": "none", "maxHeight": "800px", "overflowY": "auto", "backgroundColor": "#e5ecf6", "padding": "10px", "borderRadius": "5px", "border": "1px solid #d1d1d1"}, children=[
            # filter and selection counts
            html.Div([
                html.Span(id='filter_count_text', style={"marginRight": "20px", "fontWeight": "bold"}),
                html.Span(id='selected_count_text', style={"fontWeight": "bold", "marginRight": "12px"}),
            ], style={"marginBottom": "8px"}),
            html.Div(
                AgGrid(
                    id='dataset_grid',
                    rowData=[],
                    columnDefs=[],
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
                    style={'width': '100%', 'height': '400px'},
                    enableEnterpriseModules=False,
                ),
                style={"overflowX": "auto", "width": "100%"}
            )
        ]),
        
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
        
        # Generate figure button
        html.Div([
            html.Button("Generate Figure", id="generate_btn", n_clicks=0, disabled=False,
                         style={"backgroundColor": "#007bff", "color": "white", "border": "1px solid #e0e0e0", "borderRadius": "8px", "padding": "3px 8px", "cursor": "pointer"}),
            html.Span("", id="generate_info", style={"marginLeft": "10px", "fontWeight": "normal", "color": "#444"})
        ], id="generate_button_div", style={"display": "none", "textAlign": "center", "marginBottom": "15px"}),
        
        # Warning area for Generate action
        html.Div(id='generate_warning', children="", style={"textAlign": "center", "marginBottom": "10px"}),
        
        # Figure output
        html.Div(id="figure_div", style={"display": "none"}, children=[
            dcc.Loading(dcc.Graph(id="figure_graph"), type="default")
        ]),
        
        # Graph type selector - appears AFTER figure generation for categorical × categorical
        html.Div([
            html.Div([
                html.Span("Switch view:", style={"fontWeight": "500", "marginRight": "15px", "color": "#333"}),
                dcc.RadioItems(
                    id='cat-cat-graph-type',
                    options=[
                        {'label': ' 📊 Bar Chart', 'value': 'bar'},
                        {'label': ' 🔥 Heatmap', 'value': 'heatmap'}
                    ],
                    value='bar',
                    inline=True,
                    labelStyle={"marginRight": "20px", "cursor": "pointer"},
                    inputStyle={"marginRight": "5px"}
                ),
            ], style={
                "display": "flex", 
                "alignItems": "center", 
                "justifyContent": "center",
                "padding": "12px 20px",
                "backgroundColor": "#f8f9fa",
                "borderRadius": "8px",
                "border": "1px solid #dee2e6",
                "marginTop": "15px"
            }),
        ], id="graph-type-selector", style={"display": "none"}),
    ]
)





# ====== HELPERS ======

# Validate table name against whitelist
def validate_table_name(table_name):
    if table_name not in ALLOWED_TABLES:
        raise ValueError(f"Invalid table name: {table_name}")
    return table_name
    
# Get approximate row count using sys.partitions
def get_table_row_count(table_name):
    try:
        validate_table_name(table_name)
        query = f"""
        SELECT SUM(p.rows) AS row_count
        FROM sys.partitions p
        INNER JOIN sys.objects o ON p.object_id = o.object_id
        WHERE o.name = '{table_name}' 
          AND p.index_id IN (0, 1)
        """
        result = fetch_data_from_sql(query)
        if result is not None and not result.empty:
            return int(result.iloc[0]['row_count'])
        return None
    except Exception as e:
        print(f"Error fetching row count for {table_name}: {e}")
        return None
    
# Get column data types from INFORMATION_SCHEMA
def get_column_types(table_name):
    try:
        validate_table_name(table_name)
        query = f"""
        SELECT COLUMN_NAME, DATA_TYPE 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = '{table_name}'
        ORDER BY ORDINAL_POSITION
        """
        result = fetch_data_from_sql(query)
        if result is not None and not result.empty:
            return dict(zip(result['COLUMN_NAME'], result['DATA_TYPE']))
        return {}
    except Exception as e:
        print(f"Error fetching column types for {table_name}: {e}")
        return {}

# Determine if column should be treated as numeric
def is_column_numeric(col_name, sql_type, df):
    # Uses MSSQL type first, then pandas detection for VARCHAR/TEXT.
    # Known numeric types in SQL Server
    numeric_types = {
        'int', 'bigint', 'smallint', 'tinyint',
        'decimal', 'numeric', 'float', 'real',
        'money', 'smallmoney'
    }
    
    if sql_type.lower() in numeric_types:
        return True
    
    # For VARCHAR/TEXT types, use pandas detection
    if sql_type.lower() in ('varchar', 'nvarchar', 'char', 'nchar', 'text', 'ntext'):
        col_series = df[col_name]
        try:
            sample = pd.to_numeric(col_series.dropna().head(TYPE_DETECTION_SAMPLE_SIZE), errors='coerce')
            if len(sample) > 0 and sample.notna().sum() / float(len(sample)) >= NUMERIC_THRESHOLD:
                return True
        except Exception:
            pass
    
    return False

# Apply AG Grid filter model to DataFrame
def apply_filter_model(df, filter_model):
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

# Get DataFrame for plotting with priority: selected > filtered > all > SQL.
def _get_data_for_plotting(selected_table, x_var, y_var, row_count, 
                           row_data, selected_rows, filter_model):
    # Priority 1: Use user-selected rows if any
    if selected_rows and len(selected_rows) > 0:
        return pd.DataFrame(selected_rows)
    
    # Priority 2: Apply filter model to grid data if filters exist
    if row_data and filter_model:
        df = pd.DataFrame(row_data)
        df_filtered = apply_filter_model(df, filter_model)
        if not df_filtered.empty:
            return df_filtered
    
    # Priority 3: Use all grid data
    if row_data:
        return pd.DataFrame(row_data)
    
    # Priority 4: Fetch from SQL as fallback
    if selected_table:
        try:
            validate_table_name(selected_table)
            query = f"SELECT TOP {row_count} [{x_var}], [{y_var}] FROM [dbo].[{selected_table}]"
            df = fetch_data_from_sql(query)
            return df[[x_var, y_var]].dropna() if df is not None else None
        except Exception as e:
            print(f"Error fetching data for plotting: {e}")
            return None
    
    return None

def _create_figure_by_type(df, x_var, y_var, graph_type='bar'):    
    x_is_numeric = is_numeric_dtype(df[x_var])
    y_is_numeric = is_numeric_dtype(df[y_var])
    
    # Case 1: Both numeric -> scatter plot
    if x_is_numeric and y_is_numeric:
        fig = px.scatter(df, x=x_var, y=y_var, title=f"{x_var} vs {y_var}")
        return dcc.Graph(figure=fig)
    
    # Case 2: One numeric, one categorical -> bar chart
    if x_is_numeric or y_is_numeric:
        numeric_var = x_var if x_is_numeric else y_var
        categorical_var = y_var if x_is_numeric else x_var
        
        df_agg = df.groupby(categorical_var)[numeric_var].mean().reset_index()
        fig = px.bar(df_agg, x=categorical_var, y=numeric_var, 
                     title=f"Mean {numeric_var} by {categorical_var}")
        return dcc.Graph(figure=fig)
    
    # Case 3: Both categorical -> bar OR heatmap based on selection
    if graph_type == 'heatmap':
        fig = px.density_heatmap(df, x=x_var, y=y_var, 
                                   title=f"Heatmap of {x_var} vs {y_var}")
    else:  # bar
        fig = px.bar(df, x=x_var, color=y_var, barmode='group', 
                     title=f"{x_var} by {y_var}")
    
    return dcc.Graph(figure=fig)




# ====== CALLBACKS ======

# Track tab selection state
@callback(
    Output('dataset-tab-active', 'data'),
    [Input('main-tabs', 'value')]  
)
def set_tab_active(tab_value):
    return tab_value == 'dataset-tab'

# Reset all components when tab is switched
@callback(
    [Output('dataset_dropdown', 'value', allow_duplicate=True),
     Output('options', 'options', allow_duplicate=True),
     Output('options', 'value', allow_duplicate=True),
     Output('row_count', 'value', allow_duplicate=True),
     Output('x_variable_dropdown', 'value', allow_duplicate=True),
     Output('y_variable_dropdown', 'value', allow_duplicate=True),
     Output('figure_div', 'children', allow_duplicate=True), 
     Output('figure_div', 'style', allow_duplicate=True),
     Output('generate_btn', 'n_clicks', allow_duplicate=True),
     Output('graph-type-selector', 'style', allow_duplicate=True),
     Output('cat-cat-graph-type', 'value', allow_duplicate=True)],
    [Input('dataset-tab-active', 'data')],
    prevent_initial_call=True
)
def reset_tab_data(is_active):
    if is_active:
        raise PreventUpdate
    # Reset all controls when leaving the tab
    return None, [], [], 20, None, None, [], {"display": "none"}, 0, {"display": "none"}, 'bar'

# Fetch and cache table metadata when table is selected
@callback(
    [Output('table-metadata-store', 'data'),
     Output('options', 'options', allow_duplicate=True), 
     Output('options', 'value', allow_duplicate=True), 
     Output('columns_container', 'style'),
     Output('dataset-error-message', 'children', allow_duplicate=True)],
    [Input('dataset_dropdown', 'value')],
    [State('table-metadata-store', 'data')],
    prevent_initial_call=True
)
def fetch_table_metadata(selected_table, metadata_store):
    if selected_table is None:
        return metadata_store, [], [], {"display": "none"}, ""
    
    try:
        validate_table_name(selected_table)
        
        # Check if metadata already cached
        if selected_table in metadata_store:
            cached = metadata_store[selected_table]
            cols = cached['columns']
            opts = [{'label': c, 'value': c} for c in cols]
            return metadata_store, opts, cols, {"display": "block", "marginBottom": "15px"}, ""
        
        # Fetch metadata
        row_count = get_table_row_count(selected_table)
        column_types = get_column_types(selected_table)
        
        if not column_types:
            return metadata_store, [], [], {"display": "none"}, "Error: Could not fetch table columns"
        
        # Store metadata
        metadata_store[selected_table] = {
            'row_count': row_count,
            'column_types': column_types,
            'columns': list(column_types.keys())
        }
        
        cols = list(column_types.keys())
        opts = [{'label': c, 'value': c} for c in cols]
        return metadata_store, opts, cols, {"display": "block", "marginBottom": "15px"}, ""
        
    except Exception as e:
        error_msg = f"Error loading table: {str(e)}"
        print(error_msg)
        return metadata_store, [], [], {"display": "none"}, error_msg

# Reset dependent components when table changes
@callback(
    [Output('x_variable_dropdown', 'value', allow_duplicate=True), 
     Output('y_variable_dropdown', 'value', allow_duplicate=True),
     Output('figure_div', 'children', allow_duplicate=True), 
     Output('figure_div', 'style', allow_duplicate=True),
     Output('graph-type-selector', 'style', allow_duplicate=True),
     Output('cat-cat-graph-type', 'value', allow_duplicate=True)],
    [Input('dataset_dropdown', 'value')],
    prevent_initial_call=True
)
def reset_dependent_components(selected_table):
    return None, None, [], {"display": "none"}, {"display": "none"}, 'bar'

# Handle Select All and Deselect All buttons
@callback(
    Output('options', 'value', allow_duplicate=True),
    [Input('select_all_btn', 'n_clicks'), 
     Input('deselect_all_btn', 'n_clicks')],
    [State('options', 'options')],
    prevent_initial_call=True
)
def handle_select_buttons(select_all_clicks, deselect_all_clicks, current_options):
    trigger_id = ctx.triggered_id if ctx.triggered_id else 'no_trigger'
    
    if trigger_id == 'select_all_btn' and current_options:
        return [opt['value'] for opt in current_options]
    if trigger_id == 'deselect_all_btn':
        return []
    
    raise PreventUpdate

# Update variable dropdown options based on selected columns
@callback(
    [Output('x_variable_dropdown', 'options'), Output('y_variable_dropdown', 'options')],
    Input('options', 'options')
)
def update_variable_dropdown_options(column_options):
    return column_options, column_options

# Hide graph type selector and figure when variables change
@callback(
    [Output('figure_div', 'style', allow_duplicate=True),
     Output('graph-type-selector', 'style', allow_duplicate=True),
     Output('cat-cat-graph-type', 'value', allow_duplicate=True)],
    [Input('x_variable_dropdown', 'value'),
     Input('y_variable_dropdown', 'value')],
    prevent_initial_call=True
)
def hide_figure_on_variable_change(x_var, y_var):
    """Hide figure and toggle when user changes variables."""
    return {"display": "none"}, {"display": "none"}, 'bar'

# Update max rows info from cached metadata
@callback(
    [Output('max_rows_info', 'children'), Output('row_count', 'max')],
    [Input('dataset_dropdown', 'value'),
     Input('table-metadata-store', 'data')],
    prevent_initial_call=True
)
def update_row_count_info(selected_table, metadata_store):
    if selected_table is None or selected_table not in metadata_store:
        return "", 1000
    
    row_count = metadata_store[selected_table].get('row_count')
    if row_count:
        return f"(Max: {row_count:,} rows available)", row_count
    return "", 1000

# Update data table based on selections
@callback(
    [Output('dataset_grid', 'rowData'), 
     Output('dataset_grid', 'columnDefs'), 
     Output('row_count_container', 'style'),
     Output('placeholder_message', 'style'), 
     Output('dataset_container', 'style'),
     Output('variable_selector', 'style'), 
     Output('generate_button_div', 'style'),
     Output('dataset-error-message', 'children', allow_duplicate=True)],
    [Input('dataset_dropdown', 'value'), 
     Input('options', 'value'), 
     Input('row_count', 'value')],
    [State('options', 'options'),
     State('table-metadata-store', 'data')],
    prevent_initial_call=True
)
def update_output(selected_table, selected_columns, row_count, column_options, metadata_store):
    no_display = {"display": "none"}
    
    if selected_table is None:
        return [], [], no_display, {"display": "block"}, no_display, no_display, no_display, ""
    
    try:
        validate_table_name(selected_table)
        
        # Get columns to display
        if not selected_columns:
            cols = [opt['value'] for opt in column_options]
        else:
            cols = selected_columns
        
        # Validate and cap row count
        if row_count is None or row_count < 1:
            row_count = 20
        
        # Get metadata
        metadata = metadata_store.get(selected_table, {})
        total_rows = metadata.get('row_count', 1000)
        row_count = min(row_count, total_rows) if total_rows else row_count
        column_types = metadata.get('column_types', {})
        
        # Fetch data
        cols_sql = ", ".join([f"[{c}]" for c in cols]) if cols else "*"
        query = f"SELECT TOP {row_count} {cols_sql} FROM [dbo].[{selected_table}]"
        df = fetch_data_from_sql(query)
        
        if df is None or df.empty:
            return [], [], no_display, {"display": "block"}, no_display, no_display, no_display, "Error: No data returned from query"
        
        row_data = df.to_dict('records')

        # Build column definitions
        column_defs = []
        
        # Checkbox column
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

        # Data columns with appropriate filters
        for c in df.columns:
            sql_type = column_types.get(c, 'varchar')
            is_num = is_column_numeric(c, sql_type, df)

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
        
        return (row_data, column_defs, {"display": "block", "margin": "10px 0"}, 
                {"display": "none"}, 
                {"display": "block", "maxHeight": "800px", "overflowY": "auto", "backgroundColor": "#e5ecf6", "padding": "10px", "borderRadius": "5px", "border": "1px solid #d1d1d1"}, 
                {"display": "block", "marginBottom": "15px"}, 
                {"display": "block"},
                "")
                
    except Exception as e:
        error_msg = f"Error loading data: {str(e)}"
        print(error_msg)
        return [], [], no_display, {"display": "block"}, no_display, no_display, no_display, error_msg

# Generate figure based on variable types and graph type selection
@callback(
    [Output('figure_div', 'children', allow_duplicate=True), 
     Output('figure_div', 'style', allow_duplicate=True),
     Output('generate_warning', 'children', allow_duplicate=True),
     Output('graph-type-selector', 'style', allow_duplicate=True)],
    [Input('generate_btn', 'n_clicks'),
     Input('cat-cat-graph-type', 'value')],
    [State('dataset_dropdown', 'value'),
     State('x_variable_dropdown', 'value'),
     State('y_variable_dropdown', 'value'),
     State('row_count', 'value'),
     State('dataset_grid', 'rowData'), 
     State('dataset_grid', 'selectedRows'), 
     State('dataset_grid', 'filterModel')],
    prevent_initial_call=True)
def generate_figure(n_clicks, graph_type, selected_table, x_var, y_var, row_count, row_data, selected_rows, filter_model):    
    # Only generate on button click, not on graph type change
    trigger_id = ctx.triggered_id if ctx.triggered_id else None
    if trigger_id != 'generate_btn' and trigger_id != 'cat-cat-graph-type':
        raise PreventUpdate
    
    # Validate inputs
    if not n_clicks or selected_table is None:
        raise PreventUpdate
    
    if x_var is None or y_var is None:
        warning_msg = html.Div(
            "Error: Please select an X and Y variable",
            style={"color": "red", "fontWeight": "bold", "textAlign": "center"}
        )
        return [], {"display": "none"}, warning_msg, {"display": "none"}
    
    try:
        # Get data with priority: selected rows > filtered rows > all rows > SQL fetch
        df = _get_data_for_plotting(selected_table, x_var, y_var, row_count, 
                                     row_data, selected_rows, filter_model)
        
        if df is None or df.empty:
            warning_msg = html.Div(
                "Warning: No data available for plotting",
                style={"color": "red", "fontWeight": "bold", "textAlign": "center"}
            )
            return [], {"display": "none"}, warning_msg, {"display": "none"}
        
        # Check if both variables are categorical
        x_is_numeric = is_numeric_dtype(df[x_var])
        y_is_numeric = is_numeric_dtype(df[y_var])
        both_categorical = not x_is_numeric and not y_is_numeric
        
        # Generate appropriate figure based on variable types
        graph = _create_figure_by_type(df, x_var, y_var, graph_type)
        
        # Show toggle only for categorical × categorical
        if both_categorical:
            toggle_style = {"display": "block"}
        else:
            toggle_style = {"display": "none"}
        
        return graph, {"display": "block"}, "", toggle_style
        
    except Exception as e:
        error_msg = html.Div(
            f"Error generating figure: {str(e)}",
            style={"color": "red", "fontWeight": "bold", "textAlign": "center"}
        )
        print(f"Error in generate_figure: {e}")
        return [], {"display": "none"}, error_msg, {"display": "none"}

# Update filtered and selected row counts
@callback(
    [Output('filter_count_text', 'children'), 
     Output('selected_count_text', 'children')],
    [Input('dataset_grid', 'rowData'), 
     Input('dataset_grid', 'selectedRows'), 
     Input('dataset_grid', 'filterModel')]
)
def update_table_counts(row_data, selected_rows, filter_model):
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