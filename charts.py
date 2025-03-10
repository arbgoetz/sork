import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from dash import html
from scipy import stats
from plotly.data import gapminder
from database import fetch_data_from_sql
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Get main table
table_options = os.getenv("TABLE_OPTIONS", "").split(",")
default_table = os.getenv("MAIN_TABLE")

db_df = fetch_data_from_sql(f"SELECT TOP 20 * FROM [dbo].[{default_table}]")

def create_database_Table(num, selected_columns=None, row_count=20):
    if num is None or num < 0 or num >= len(table_options):
        return go.Figure()  # Return empty figure if index is invalid

    selected_table = table_options[num]
    
    try:
        # Use the row_count parameter to limit the number of rows
        db_df = fetch_data_from_sql(f"SELECT TOP {row_count} * FROM [dbo].[{selected_table}]")
    except Exception as e:
        print(f"Error fetching data from table {selected_table}: {e}")
        return go.Figure()  # Return an empty figure if query fails

    # Filter selected columns
    if selected_columns:
        db_df = db_df[selected_columns]  # Show only selected columns

    # Calculate if horizontal scrolling is needed (if more than 15 columns)
    enable_scrolling = len(db_df.columns) > 15
    
    # Set fixed column width for better readability when scrolling
    column_width = 150 if enable_scrolling else None
    
    # Create the table figure
    fig = go.Figure(data=[go.Table(
        header=dict(
            values=db_df.columns,
            align='left',
            fill_color='#d1d1d1',
            font=dict(color='black', size=12),
            height=30
        ),
        cells=dict(
            values=db_df.values.T,
            align='left',
            fill_color='#f9f9f9',
            font=dict(color='black', size=11),
            height=25
        ),
        columnwidth=column_width  # Set fixed column width when scrolling
    )])
    
    # Update layout with improved styling
    fig.update_layout(
        paper_bgcolor="#e5ecf6", 
        plot_bgcolor="#e5ecf6",
        margin={"t":40, "l":0, "r":0, "b":0},  # Adjust top margin for title
        height=min(600, 150 + len(db_df) * 25),  # Dynamic height based on number of rows
        title={
            'text': f"Showing {len(db_df)} rows from {selected_table}",
            'y':0.98,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        # Enable horizontal scrolling if needed
        autosize=True
    )
    
    # Add horizontal scrolling settings when needed
    if enable_scrolling:
        # Calculate the width needed for all columns at 150px each plus some buffer
        total_width = len(db_df.columns) * 150
        fig.update_layout(
            width=total_width,
            xaxis=dict(
                rangeslider=dict(visible=True),
                automargin=True
            )
        )
    
    return fig


    if not selected_column_1 or not selected_column_2:
        return px.scatter()
    
    if selected_column_1 not in db_df.columns or selected_column_2 not in db_df.columns:
        raise ValueError(f"One or more selected columns not found in data frame.")
    
    filtered_df = db_df[~(db_df[selected_column_1].isna() | db_df[selected_column_2].isna())].copy()
    
    x = filtered_df[selected_column_1]
    y = filtered_df[selected_column_2]
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    
    x_range = np.linspace(x.min(), x.max(), 100)
    y_predicted = slope * x_range + intercept

    fig = px.scatter(filtered_df, x=selected_column_1, y=selected_column_2,
                    title=f"Linear Regression: {selected_column_2} vs {selected_column_1}")
    
    fig.add_scatter(x=x_range, y=y_predicted, mode='lines', name='Regression Line',
                   line=dict(color='red'))
    
    r_squared = r_value ** 2
    eq_text = f"y = {slope:.2f}x + {intercept:.2f}"
    r2_text = f"R² = {r_squared:.3f}"
    fig.update_layout(
        title=f"Linear Regression: {selected_column_2} vs {selected_column_1}<br><sub>{eq_text} | {r2_text}</sub>",
        paper_bgcolor="#e5ecf6",
        height=600,
        xaxis_title=selected_column_1,
        yaxis_title=selected_column_2,
        showlegend=True
    )
    
    return fig