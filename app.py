from dash import dcc, html, Dash
from tabs.dataset_tab import dataset_layout
from tabs.stats import stats_layout
from tabs.upload import upload_layout
from tabs.download import download_layout
from tabs.map import map_layout

css = ["https://cdn.jsdelivr.net/npm/bootstrap@5.3.1/dist/css/bootstrap.min.css"]
app = Dash(name="Sork Lab Dashboard", external_stylesheets=css)

# Describe App Layout
app.layout = html.Div([
    html.Div(
        html.H1("Sork Lab Dashboard", className="text-center fw-bold"),
        style={"backgroundColor":'white', "padding": "15px"}
    ),
    html.Div([
        html.Br(),
        dcc.Tabs([
            dataset_layout,
            stats_layout,
            map_layout,
            upload_layout,
            download_layout,
        ], className="mb-4") 
    ], className="col-8 mx-auto"),
    html.Footer(
        html.Div("Sork Lab Dashboard © 2025", className="text-center text-muted py-3"),
        style={"backgroundColor": "#f5f5f5", "borderTop": "1px solid #e3e3e3", "width": "100%", "position": "fixed", "bottom": "0"}
    )
], style={"background-color": "#e5ecf6", "minHeight": "100vh", "paddingBottom": "60px"}) 

if __name__ == "__main__":
    app.run(debug=True)