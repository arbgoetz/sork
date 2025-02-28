from dash import dcc
from charts import gapminder_df, db_df
import numpy as np

continents = gapminder_df.Continent.unique()
years = gapminder_df.Year.unique()

cont_population = dcc.Dropdown(id="cont_pop", options=continents, value="Asia", clearable=False)
year_population = dcc.Dropdown(id="year_pop", options=years, value=1952, clearable=False)

cont_gdp = dcc.Dropdown(id="cont_gdp", options=continents, value="Asia", clearable=False)
year_gdp = dcc.Dropdown(id="year_gdp", options=years, value=1952, clearable=False)

cont_life_exp = dcc.Dropdown(id="cont_life_exp", options=continents, value="Asia", clearable=False)
year_life_exp = dcc.Dropdown(id="year_life_exp", options=years, value=1952, clearable=False)

year_map = dcc.Dropdown(id="year_map", options=years, value=1952, clearable=False)
var_map = dcc.Dropdown(
    id="var_map",
    options=["Population", "GDP per Capita", "Life Expectancy"],
    value="Life Expectancy", clearable=False
)

# Stats page widgets
dropdown_analysis_type = dcc.Dropdown(
    id="analysis_type",
    options=[
        {'label': 'Linear Regression', 'value': 'linreg'}, 
        {'label': 'PCA (Principal Component Analysis)', 'value': 'pca'},
        {'label': 'Summary Statistics', 'value': 'summarystat'}
    ],
    value=None, 
    placeholder='Select Analysis Type'
)

linreg_dropdown_x = dcc.Dropdown(
    id="linreg_x", 
    options=[{'label':col, 'value':col} for col in db_df.columns],
    # value="Height_cm",
    placeholder='Select x-axis variable'
)

linreg_dropdown_y = dcc.Dropdown(
    id="linreg_y", 
    options=[{'label':col, 'value':col} for col in db_df.columns],
    # value="Height_cm",
    placeholder='Select y-axis variable'
)

summarystat_dropdown = dcc.Dropdown(
    id="summarystat_dropdown",
    options=[{'label':col, 'value':col} for col in db_df[['Height_cm', 'BDiam_mm', 'DBH_1', 'DBH_2', 'DBH_3', 'DBH_4', 'DBH_5', 'DBH_6', 'DBH_7', 'DBH_8', 'Alive_new', 'Multistem_yn', 'Gopher_damage', 'Powderymildew_yn', 'Brownspots', 'Yellowspots', 'Observation_date', 'Site']]], # columns we can perform meaningful summary stats on
    placeholder="Select column"
)

pca_dropdown = dcc.Dropdown(
    id="pca_dropdown", 
    options= [{'label':col, 'value':col} for col in db_df.columns],
    multi=True,
    placeholder="Select variables for CA analysis"
)