import plotly.express as px
import plotly.graph_objects as go
from plotly.data import gapminder
from database import fetch_data_from_sql

gapminder_df = gapminder(datetimes=True, centroids=True, pretty_names=True)
gapminder_df["Year"] = gapminder_df.Year.dt.year

db_df = fetch_data_from_sql("SELECT TOP 5 * FROM [dbo].[2013-2024 census long_coreonly_fordb_101624]")

def create_database_Table(columns = None):
    fig = go.Figure(data=[go.Table(
        header=dict(values=db_df.columns, align='left'),
        cells=dict(values=db_df.values.T, align='left'))])
    fig.update_layout(paper_bgcolor="#e5ecf6", margin={"t":0, "l":0, "r":0, "b":0}, height=700)
    return fig

def create_stats_chart(continent="Asia", year=1952, ):
    filtered_df = gapminder_df[(gapminder_df.Continent==continent) & (gapminder_df.Year==year)]
    filtered_df = filtered_df.sort_values(by="Population", ascending=False).head(15)

    fig = px.bar(filtered_df, x="Country", y="Population", color="Country",
                   title="Country {} for {} Continent in {}".format("Population", continent, year),
                   text_auto=True)
    fig.update_layout(paper_bgcolor="#e5ecf6", height=600)
    return fig
