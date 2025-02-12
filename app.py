from dash import dcc, html, Dash
from tabs.dataset_tab import dataset_layout
from tabs.stats import stats_layout

css = ["https://cdn.jsdelivr.net/npm/bootstrap@5.3.1/dist/css/bootstrap.min.css"]
app = Dash(name="Sork Lab Dashboard", external_stylesheets=css)

# Define the layout
app.layout = html.Div([
    html.Div([
        html.H1("Sork Lab Dashboard", className="text-center fw-bold m-2"),
        html.Br(),
        dcc.Tabs([
            dataset_layout,
            stats_layout,
        ])
    ], className="col-8 mx-auto"),
], style={"background-color": "#e5ecf6", "height": "100vh"})

if __name__ == "__main__":
    app.run(debug=True)
