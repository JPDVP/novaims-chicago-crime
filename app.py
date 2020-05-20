import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import pandas as pd
import numpy as np
import plotly.graph_objs as go
import json
from urllib.request import urlopen
from math import ceil, log10


# paths for the dataset and related files
github_url = 'https://raw.githubusercontent.com/JPDVP/DV_IMS_2019/master/'
summary_file = 'dataset_files/Crimes_Summary.csv'
year_summary = 'dataset_files/{year}/Crimes_Summary_{year}.csv'
year_detail = 'dataset_files/{year}/Crimes_{year}_{ca}.csv'
geojson_path = 'chicago_areas.geojson'


# load dataset
df_summ = pd.read_csv(github_url + summary_file)
df_summ.sort_values(by=['Year','Month'], inplace=True)
df_summ['yyyy-mm'] = df_summ['Year'].apply(str) + '-' + df_summ['Month'].apply(lambda x: ('00' + str(x))[-2:])


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
unq_year = sorted(df_summ['Year'].unique())
unq_crime = sorted(df_summ['Primary Type'].unique())

min_max_year = [unq_year[0], unq_year[-1]]


### CSS ###
external_css = [
    dict(
        href='https://stackpath.bootstrapcdn.com/bootstrap/4.5.0/css/bootstrap.min.css',
        rel='stylesheet',
        integrity='sha384-9aIt2nRpC12Uk9gS9baDl411NQApFmC26EwAOH8WgZl5MYYxFfc+NcPb1dKGj7Sk',
        crossorigin='anonymous'
    )
]

# css_options
css_color_light = '#f8f9fa'


### DCC COMPONENTS ###

# dropdown Primary Type
dropdown_crimes = dcc.Dropdown(
    id='dropdown-crimes',
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

# radio arrest
check_arrest = dcc.Checklist(
    id='check-arrest',
    options=[
        {'label': 'True', 'value': 'True'},
        {'label': 'False', 'value': 'False'}
    ],
    value=['True','False'],
    labelStyle={'display':'block', 'margin':'5px'}
)

# slider for years
slider_years = dcc.RangeSlider(
    id='slider-years',
    min=unq_year[0],
    max=unq_year[-1],
    step=1,
    marks={int(year):str(year) if n % 2 == 0 else '' for (n, year) in enumerate(unq_year)},
    value=min_max_year
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
            style={'padding':1, 'margin-bottom':1, 'color':css_color_light}
        ),

        # first-row-div
        html.Div(
            # filters-div
            html.Div(
                [
                    html.Div([html.H3('Dashboard Filters:')], className='mb-2'),
                    html.Div([html.H5('Crime Type'), dropdown_crimes], className='mb-1'),
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
                        html.Div([html.H5('Arrest'),check_arrest], className='col-4 mt-3 ml-3'),
                    ], className='row mt-1 mb-3'),
                    html.Div([
                            html.H5('Year'),
                            html.Div(slider_years, className='ml-2 mt-1')
                        ],
                        className='mt-3 mb-3'
                    )
                ],
                id='filters-div',
                className='col-3 p-4 shadow bg-light rounded',
            ),
            id='row-div-1',
            className='row mr-2 ml-2 mt-3 mb-3'
        ),
        html.Div(
            [
                html.Div([dcc.Graph(id='graph-timeline')], className='col-6 shadow bg-light rounded')
            ],
            id='row-div-2',
            className='row mr-2 ml-2 mt-3 mb-3'
        )
    ], id='outer-div', className='mb-2 mr-2 ml-2 p-1')
], className='bg-dark')



### FUNCTIONS ###


# utility functions
def round_axis(value):
    scale = 10**int(log10(value))
    max_axis = ceil(value / scale) * scale
    return min(max_axis, max(max_axis - scale/2, value))

def calculate_max(df, groupby_fields):
    return max(df.groupby(groupby_fields)['Count'].sum())


# filter functions
def filter_date(df, year_list):
    # returns the df filtered by the min and max year in year_list
    return (df['Year'] >= min(year_list)) & (df['Year'] <= max(year_list))

def filter_ca(df, ca):
    # return the df filtered by the Community Area
    return df['Community Area'] == ca

def filter_crimes(df, list_crimes):
    # return the df filtered by the list of types of crime
    return df['Primary Type'].isin(list_crimes)

def filter_arrest(df, list_arrest):
    # return the df filtered by arrests or not
    return df['Arrest'].isin(list_arrest)

def filter_df(df, year_list=min_max_year, ca=None, list_crimes=[], list_arrest=[True,False]):
    n = len(df)
    filter_arr = np.array([True]*n)
    
    # apply year filter
    if year_list != min_max_year:
        filter_arr &= filter_date(df, year_list)
    # apply ca filter
    if ca is not None:
        filter_arr &= filter_ca(df, ca)
    # apply crime filter
    if list_crimes != []:
        filter_arr &= filter_crimes(df, list_crimes)
    # apply arrest filter
    if list_arrest != [True,False] and list_arrest != []:
        filter_arr &= filter_arrest(df, list_arrest)
    
    return df[filter_arr]


## TIMELINE
def timeline_by_crime(df):
    df_group = df.groupby(['yyyy-mm','Primary Type'])['Count'].sum().reset_index()
    pivot = pd.pivot_table(df_group, values='Count', index='yyyy-mm', columns='Primary Type')
    return [go.Scatter(x=pivot.index, y=pivot[col], name=col) for col in pivot.columns]

def timeline_total(df):
    # calculates the total trace
    timeline_series = df.groupby('yyyy-mm')['Count'].sum()
    return [go.Scatter(x=timeline_series.index, y=timeline_series.values, name='TOTAL CRIMES')]


def get_timeline(df, include_details):
    # data definition
    if include_details:
        timeline_data = timeline_by_crime(df)
        max_y_axis = round_axis(calculate_max(df, ['yyyy-mm','Primary Type']))
    else:
        timeline_data = timeline_total(df)
        max_y_axis = round_axis(calculate_max(df, ['yyyy-mm']))

    # layout definition
    timeline_layout = go.Layout(
        title=dict(text='Crimes Timeline'),
        xaxis = dict(
            rangeslider_visible=True,
            tickformatstops = [
                dict(dtickrange=[None, 'M6'], value='%Y-%b'),
                dict(dtickrange=['M6', None], value='%Y')
            ]
        ),
        #yaxis = dict(range=[0, max_y_axis]),
        showlegend=(len(timeline_data) > 1),     # show legend only if details are included
        legend=dict(
            orientation='h',
            x=0,
            y=-0.4,
            xanchor='left',
            yanchor='top'
        ),
        paper_bgcolor=css_color_light,
        plot_bgcolor=css_color_light,
        margin=dict(l=10,r=10,t=60,b=30)
    )

    return go.Figure(data=timeline_data, layout=timeline_layout)


### CALLBACKS ###

@app.callback(
    Output('graph-timeline','figure'),
    [
        Input('slider-years','value'),
        Input('dropdown-ca','value'),
        Input('dropdown-crimes','value'),
        Input('check-arrest','value')
    ]
)
def get_figures(year_list, ca, list_crimes, arrest):
    list_arrest = list(map(lambda x: x == 'True', arrest))
    df_filtered = filter_df(df_summ, year_list, ca, list_crimes, list_arrest)

    include_details = (list_crimes != [])

    return get_timeline(df_filtered, include_details)


  
@app.callback(
    Output('dropdown-crimes', 'value'),
    [Input('slider-top-crimes', 'value')]
)
def return_top_crimes(top):
    return df_summ.groupby('Primary Type')['Count'].sum().nlargest(top).index  



### RUN ###

if __name__ == '__main__':
    app.run_server(debug=True)
