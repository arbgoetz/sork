from dash import dcc, html, Dash
from tabs.dataset import dataset_layout
from tabs.stats import stats_layout
from tabs.upload import upload_layout
from tabs.download import download_layout
from tabs.map import map_layout
from tabs.joins import joins_layout

css = ["https://cdn.jsdelivr.net/npm/bootstrap@5.3.1/dist/css/bootstrap.min.css"]
app = Dash(name="Sork Lab Dashboard", external_stylesheets=css)

# Describe App Layout
app.layout = html.Div([
    # Main content wrapper with flexible height
    html.Div([
        # Header
        html.Div(
            html.H1("Sork Lab Dashboard", className="text-center fw-bold"),
            style={"backgroundColor": 'white', "padding": "15px"}
        ),
        # Tab content container
        html.Div([
            html.Br(),
            # Give the tabs a unique ID that all components can access
            dcc.Tabs(id='main-tabs', value='dataset-tab', children=[
                dataset_layout,
                stats_layout,
                joins_layout,
                map_layout,
                upload_layout,
                download_layout,
            ], className="mb-4") 
        ], className="col-8 mx-auto", style={"minHeight": "calc(100vh - 200px)"})
    ], style={"flex": "1 0 auto"}),
    
    # Footer that stays at the bottom
    html.Footer(
        html.Div("Sork Lab Dashboard © 2025", className="text-center text-muted py-3"),
        style={
            "backgroundColor": "#f5f5f5", 
            "color": "#e3e3e3", 
            "padding": "20px", 
            "width": "100%",
            "marginTop": "40px"
        }
    )
], style={
    "background-color": "#e5ecf6", 
    "minHeight": "100vh",
    "display": "flex",
    "flexDirection": "column"
}) 

if __name__ == "__main__":
    app.run(debug=True)