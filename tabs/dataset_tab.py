from dash import dcc, html, Input, Output, callback
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
        dcc.Dropdown(table_options, id="dataset_dropdown", placeholder="Select a table"),
        dcc.Dropdown(id="options", placeholder="Select columns to include in table", multi=True),
        dcc.Graph(id="dataset")
    ],
    label = "Dataset"
)

@callback(
    Output('options', 'options'),  # Populate column selection dropdown
    Input('dataset_dropdown', 'value')
)
def update_column_options(selected_table):
    """Fetches column names dynamically based on selected table."""
    if selected_table is None:
        return []

    try:
        db_df = fetch_data_from_sql(f"SELECT TOP 1 * FROM [dbo].[{selected_table}]")  # Fetch sample row
        return [{'label': col, 'value': col} for col in db_df.columns]
    except Exception as e:
        print(f"Error fetching columns for table {selected_table}: {e}")
        return []

@callback(
    Output('dataset', 'figure'),
    Input('dataset_dropdown', 'value'),
    Input('options', 'value')  # Selected columns
)
def update_output(selected_table, selected_columns):
    if selected_table is None:
        return {}

    table_index = table_options.index(selected_table)
    return create_database_Table(table_index, selected_columns)