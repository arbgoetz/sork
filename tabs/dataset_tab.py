from dash import dcc, html, Input, Output, callback
from charts import create_database_Table

dataset_layout = dcc.Tab(
    [
        html.Br(), 
        dcc.Graph(id="dataset", figure=create_database_Table())
    ],
    label="Dataset"
)