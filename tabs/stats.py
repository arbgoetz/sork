from dash import dcc, html, Input, Output, callback
from widgets import cont_population, year_population
from charts import create_stats_chart

stats_layout = dcc.Tab([
    html.Br(), "Continent", cont_population, "Year", year_population, html.Br(),
    dcc.Graph(id="Stats and Plots")
], label="Stats and Plots")

@callback(
    Output("Stats and Plots", "figure"),
    [Input("cont_pop", "value"), Input("year_pop", "value")]
)
def update_stats_chart(continent, year):
    return create_stats_chart(continent, year)