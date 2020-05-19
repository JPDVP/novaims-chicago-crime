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
    options=[{'label':v, 'value':k} for (k,v) in ca_names.items()]
)

slider_top_crimes = dcc.Slider(
    id='slider-top-crimes',
    min=0,
    max=10,
    marks={i:str(i) if i!=0 else 'All' for i in range(11)},
    value=0
)

# dropdown_top_crimes = dcc.Dropdown(
#     id='dropdown-top-crimes',
#     options=[{'label':str(i) if i != 0 else 'All', 'value':i} for i in range(11)],
#     value=0
# )

# radio arrest
radio_arrest = dcc.RadioItems(
    options=[
        {'label': 'All', 'value': 'All'},
        {'label': 'True', 'value': 'True'},
        {'label': 'False', 'value': 'False'}
    ],
    value='All',
    labelStyle={'display':'block', 'margin':'5px'}
)

# slider for years
slider_years = dcc.RangeSlider(
    min=min(unq_year),
    max=max(unq_year),
    step=1,
    marks={int(year):str(year) if n % 2 == 0 else '' for (n, year) in enumerate(unq_year)},
    value=[min(unq_year),max(unq_year)]
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

        # first-row-div
        html.Div(
            # filters-div
            html.Div(
                [
                    html.Div([html.H3('Dashboard Filters:')], className='mt-3 mb-3'),
                    html.Div([html.H5('Crime Type'), dropdown_crime], className='mt-3 mb-1'),
                    html.Div([
                        html.Div([
                            html.Div([
                                    html.H6('Top:'),
                                    html.Div(slider_top_crimes, className='ml-2 mt-1')
                                ], 
                                className='mt-1 mb-5'
                            ),
                            html.Div([html.H5('Community Area'), dropdown_ca], className='mt-5')
                        ], className='col-7 mr-3'),
                        html.Div([html.H5('Arrest'),radio_arrest], className='col-4 mt-3 ml-3'),
                    ], className='row mt-1 mb-3'),
                    html.Div([
                            html.H5('Year'),
                            html.Div(slider_years, className='ml-2 mt-1')
                        ],
                        className='mt-3 mb-3'
                    )
                ],
                id='filters-div',
                className='col-3 mr-2 ml-2 mt-2 mb-2 p-1',
            ),
            id='first-row-div',
            className='row mr-2 ml-2 mt-2 mb-2 p-1'
        )
    ], id='outer-div', className='mb-2 mr-2 ml-2 p-1')
], className='bg-light')


@app.callback(
    Output('dropdown-crime', 'value'),
    [Input('slider-top-crimes', 'value')])
def return_top_crimes(top):
    return df.groupby('Primary Type')['Count'].sum().nlargest(top).index


if __name__ == '__main__':
    app.run_server(debug=True)