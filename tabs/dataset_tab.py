from dash import dcc, html, Input, Output, callback
from charts import create_database_Table
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Table Options
table_options = os.getenv("TABLE_OPTIONS", "").split(",")

dataset_layout = dcc.Tab(
    [
        html.Br(), 
        dcc.Dropdown(table_options, id="dataset_dropdown", placeholder="Select a table"),
        dcc.Graph(id="dataset")
    ],
    label = "Dataset"
)

@callback(
    Output('dataset', 'figure'),
    Input('dataset_dropdown', 'value')   
)
def update_output(value):
    if value is None:
        return {}
    return create_database_Table(table_options.index(value))