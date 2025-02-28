from dash import dcc, html, Input, Output, callback
from widgets import dropdown_analysis_type, linreg_dropdown_x, linreg_dropdown_y, summarystat_dropdown, pca_dropdown
from charts import create_stats_chart, create_summary_statistics, create_summary_table, create_lr_chart
import plotly.express as px

stats_layout = dcc.Tab(
    label="Stats and Plots",
    children = [
        html.Br(),
        html.Label("Analysis Type"), 
        dropdown_analysis_type,
        html.Br(),
        html.Div(id="dropdown-container", children=[summarystat_dropdown, linreg_dropdown_x, linreg_dropdown_y, pca_dropdown]),
        html.Br(),
        html.Div(id="summarystats-container"),
        dcc.Graph(id="Stats and Plots"),

        # Store components (hold selected values)
        dcc.Store(id="selected-x"),
        dcc.Store(id="selected-y"),
        dcc.Store(id="selected-summary"), 
        dcc.Store(id="selected-pca")
    ]
)

# Handle dropdown display
@callback(
    Output("dropdown-container", "children"),
    Input("analysis_type", "value")
)
def update_dropdowns(analysis_type):
    if analysis_type == "summarystat":
        return [
            html.Label("Select Column for Summary Statistics"),
            summarystat_dropdown
        ]
    elif analysis_type == "linreg":
        return html.Div([
            html.Label("Select X Variable"),
            linreg_dropdown_x,
            html.Br(),
            html.Label("Select Y Variable"),
            linreg_dropdown_y
        ])
    elif analysis_type == "pca":
        return html.Div([
            html.Label("Select PCA variables"),
            pca_dropdown, 
            html.Br()
        ])
    else:
        return html.Div()
    
# Stores (fix dynamic dropdown issue)
@callback(
    Output("selected-summary", "data"),
    Input("summarystat_dropdown", "value"),
    prevent_initial_call=True
)
def update_summary_store(value):
    return value

@callback(
    Output("selected-x", "data"),
    Input("linreg_x", "value"),
    prevent_initial_call=True
)
def update_x_store(value):
    return value

@callback(
    Output("selected-y", "data"),
    Input("linreg_y", "value"),
    prevent_initial_call=True
)
def update_y_store(value):
    return value

@callback(
    Output("selected-pca", "data"),
    Input("pca_dropdown", "value"),
    prevent_initial_call=True
)
def update_pca_store(value):
    return value