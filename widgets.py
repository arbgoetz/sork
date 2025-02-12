from dash import dcc
from charts import gapminder_df

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
