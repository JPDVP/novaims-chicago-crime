import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.graph_objs as go
import json
from urllib.request import urlopen


# paths for the dataset and related files
github_url = 'https://raw.githubusercontent.com/JPDVP/DV_IMS_2019/master/'
summary_file = 'dataset_files/Crimes_Summary.csv'
year_summary = 'dataset_files/{year}/Crimes_Summary_{year}.csv'
year_detail = 'dataset_files/{year}/Crimes_{year}_{ca}.csv'
geojson_path = 'chicago_areas.geojson'


# load dataset
df = pd.read_csv(github_url + summary_file)
df['yyyy-mm'] = df['Year'].apply(str) + '-' + df['Month'].apply(str)


# load geojson
chicago_geojson = json.load(urlopen(github_url + geojson_path))
# assign id for choropleth
for feature in chicago_geojson['features']:
    feature['id'] = int(feature['properties']['area_num_1'])

# create name dictionary for community areas
ca_names = {
    feature['id']: feature['properties']['community']
    for feature in chicago_geojson['features']
}

# get unique values
unq_year = sorted(df['Year'].unique())
unq_crime = sorted(df['Primary Type'].unique())


#
    # Multi dropdown Crime Type
    # Multi dropdown Community Area
    # Slider Year

external_css = [
    dict(
        href='https://stackpath.bootstrapcdn.com/bootstrap/4.5.0/css/bootstrap.min.css',
        rel='stylesheet',
        integrity='sha384-9aIt2nRpC12Uk9gS9baDl411NQApFmC26EwAOH8WgZl5MYYxFfc+NcPb1dKGj7Sk',
        crossorigin='anonymous'
    )
]


#### dcc Components ####

# dropdown Primary Type
dropdown_crime = dcc.Dropdown(
    id='dropdown-crime',
    options=[{'label':crime_type, 'value':crime_type} for crime_type in unq_crime],
    multi=True
)

# dropdown Community Area
dropdown_ca = dcc.Dropdown(
    id='dropdown-ca',
    options=[{'label':v, 'value':k} for (k,v) in ca_names.items()],
    multi=True
)

# slider for years
slider_years = dcc.Slider(
    min=min(unq_year),
    max=max(unq_year),
    step=1,
    marks={year:str(year) for year in unq_year},
    value=2019
)


app = dash.Dash(__name__, external_stylesheets=external_css)
server = app.server

app.layout = html.Div([
    # outer-div
    html.Div([
        # title-div
        html.Div(
            html.H1('Crime in Chicago'),
            id='title-div',
            className='row justify-content-md-center',
            style={'padding':5, 'margin-bottom':2}
        ),

        # filters-div
        html.Div(
            [
                html.H3('Dashboard Filters:'),
                html.H5('Crime Type'),
                dropdown_crime,
                html.Br(),
                html.H5('Community Area'),
                dropdown_ca,
                html.Br(),
                html.H5('Year'),
                slider_years
            ],
            id='filters-div'
        )
    ], id='outer-div', className='mb-2 mr-2 ml-2 p-1')
], className='bg-light')


if __name__ == '__main__':
    app.run_server(debug=True)