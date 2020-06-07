import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import pandas as pd
import numpy as np
import plotly.graph_objs as go
import json
from urllib.request import urlopen


# paths for the dataset and related files
github_url = 'https://raw.githubusercontent.com/JPDVP/DV_IMS_2019/master/'
summary_file = 'dataset_files/Crimes_Summary.csv'
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

# slider for map
slider_map = dcc.Slider(
    id='slider-map',
    step=1,
    included=False
)

# button
switch_button = html.Button(
    id='switch-button',
    n_clicks=0
)

### HTML Components ###
filters_div =  html.Div(
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
                html.Div([html.H5('Year'), html.Div(switch_button, className='col-5')], className='row'),
                html.Div(
                    [
                        html.Div(slider_years, id='div-slider-years', style={'display':'block'}),
                        html.Div(slider_map, id='div-slider-map', style={'display':'none'})
                    ],
                    className='mt-3'
                )
            ],
            className='mt-3'
        )
    ],
    id='filters-div',
    className='p-4 shadow bg-light rounded'
)

timeline_div = html.Div(
    dcc.Graph(id='graph-timeline'),
    id='timeline-div',
    className='shadow bg-light rounded'
)

slider_div = html.Div(
    html.Div(slider_map, className='my-auto'),
    className='shadow bg-light rounded'
)

map_div = html.Div(
    html.Div(dcc.Graph(id='graph-map'), className='my-auto'),
    className='shadow bg-light rounded'
)

bar_chart_div = html.Div(
    dcc.Graph(id='bar-chart'),
    id='bar-chart-div',
    className='shadow bg-light rounded'
)

card_title = ['Total Crimes', 'Average Crimes', 'Top Crime', 'Top Criminal Area', 'Percentage Arrests']
card_div = html.Div(
    [
        html.Div(
            [
                html.Div(title, className='text-center', style={'fontSize':'14px'}),
                html.Div(html.B(id='card-{}'.format(n+1)), className='text-center', style={'fontSize':'24px'})
            ],
            className='shadow bg-light rounded mb-4 mt-4')
        for n, title in enumerate(card_title)
    ],
    className='mr-2'
)

app = dash.Dash(__name__, external_stylesheets=external_css)
server = app.server

app.layout = html.Div(
    [
        html.Div(html.H1('Crime in Chicago'), className='row justify-content-center', style={'color':css_color_light}),
        html.Div([
            html.Div(filters_div, className='col-3 p-2'),
            html.Div(card_div, className='col-2 p-2'),
            html.Div(map_div, className='col-7 p-2')
        ],
        id='row1-div',
        className='row ml-2 mr-2'
        ),
        html.Div([
            html.Div(timeline_div, className='col-8 p-2'),
            html.Div(bar_chart_div, className='col-4 p-2')
        ],
        id='row2-div',
        className='row ml-2 mr-2')
    ],
    id='outer-div',
    className='bg-dark'
)


### FUNCTIONS ###


# filter functions
def filter_date(df, year_list):
    # returns the df filtered by the min and max year in year_list
    return (df['Year'] >= year_list[0]) & (df['Year'] <= year_list[-1])

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
    else:
        timeline_data = timeline_total(df)

    # layout definition
    timeline_layout = go.Layout(
        title=dict(text='Crimes Timeline', font=dict(size=20)),
        xaxis = dict(
            #rangeslider_visible=True,
            tickformatstops = [
                dict(dtickrange=[None, 'M6'], value='%Y-%b'),
                dict(dtickrange=['M6', None], value='%Y')
            ]
        ),
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
        margin=dict(l=20,r=20,t=60,b=30)
    )

    return go.Figure(data=timeline_data, layout=timeline_layout)


## MAP
def get_choropleth(df, ca, slider_option, year_list):
    choropleth_series = df.groupby(['Year','Community Area'])['Count'].sum()
    
    if year_list[0] > slider_option:
        series = choropleth_series.groupby('Community Area').mean()
        chart_title = 'Crime Map (average {}-{})'.format(year_list[0], year_list[-1])
    else:
        series = choropleth_series.loc[(slider_option,)]
        chart_title = 'Crime Map ({})'.format(slider_option)

    ca_labels = [ca_names.get(id_ca,'') for id_ca in series.index]
    
    # average values by community area
    data_choroplethmap = go.Choropleth(
        geojson=chicago_geojson,
        locations=series.index,
        z=series.values,
        text=ca_labels,
        colorscale='inferno',
        reversescale=True,
        marker=dict(opacity=.85),
        zauto=False,
        zmin=0,
        zmax=max(choropleth_series.values)
    )
    
    layout_choroplethmap = go.Layout(
        title=dict(text=chart_title, font=dict(size=20), x=0.5, y=0.95),
        mapbox=dict(
            layers=[
                dict(
                    source=feature,
                    below='traces',
                    type='fill',
                    fill=dict(outlinecolor='black'))
                for feature in chicago_geojson['features']
            ]
        ),
        geo=dict(fitbounds='locations', visible=False),
        paper_bgcolor=css_color_light,
        plot_bgcolor=css_color_light,
        margin=dict(l=10,r=10,t=40,b=10)
    )
    
    return go.Figure(data=data_choroplethmap, layout=layout_choroplethmap)

## BAR CHART
def get_bar_chart(df, slider_option, year_list):
    # boolean to force to take at max 10 type of crimes

    bar_series = df.groupby(['Year','Primary Type'])['Count'].sum()

    if year_list[0] > slider_option:
        series = bar_series.groupby('Primary Type').mean().sort_values(ascending=False).head(10)
        chart_title = 'Crime by Type (average {}-{})'.format(year_list[0], year_list[-1])
    else:
        series = bar_series.loc[(slider_option,)].sort_values(ascending=False).head(10)
        chart_title = 'Crime by Type ({})'.format(slider_option)

    data_bar = [
        go.Bar(x=series.index, y=series.values)
    ]

    layout_bar = go.Layout(
        title=dict(text=chart_title, font=dict(size=20), x=0.5, y=0.95),
        paper_bgcolor=css_color_light,
        plot_bgcolor=css_color_light
    )

    return go.Figure(data=data_bar, layout=layout_bar)


def calculate_metrics(df):
    
    metrics = [
        df['Count'].sum(),
        df.groupby('Year')['Count'].sum().mean(),
        df.groupby('Primary Type')['Count'].sum().nlargest(1).index[0],
        ca_names[df.groupby('Community Area')['Count'].sum().nlargest(1).index[0]],
        df[df['Arrest']]['Count'].sum() / df['Count'].sum() * 100
    ]

    metrics_format = [
        '{:,d}',
        '{:,.2f}',
        '{}',
        '{}',
        '{:,.2f}%'
    ]

    metrics = list(map(lambda x: x[1].format(x[0]).replace(',',' '), zip(metrics, metrics_format)))

    return metrics


### CALLBACKS ###

@app.callback(
    [
        Output('switch-button','children'),
        Output('div-slider-years','style'),
        Output('div-slider-map','style')
    ],
    [
        Input('switch-button','n_clicks')
    ]
)
def switch_slider(n_clicks):
    if n_clicks % 2 == 0:
        button_text = 'Select Single Year'
        visibility_slider_years = {'display':'block'}
        visibility_slider_map = {'display':'none'}
    else:
        button_text = 'Select Year Range'
        visibility_slider_years = {'display':'none'}
        visibility_slider_map = {'display':'block'}
    
    return [button_text], visibility_slider_years, visibility_slider_map


@app.callback(
    [
        Output('graph-timeline','figure'),
        Output('graph-map','figure'),
        Output('bar-chart','figure'),
        Output('card-1','children'),
        Output('card-2','children'),
        Output('card-3','children'),
        Output('card-4','children'),
        Output('card-5','children')
    ],
    [
        Input('slider-years','value'),
        Input('dropdown-ca','value'),
        Input('dropdown-crimes','value'),
        Input('check-arrest','value'),
        Input('slider-map','value')
    ]
)
def get_figures(year_list, ca, list_crimes, arrest, slider_option):
    list_arrest = list(map(lambda x: x == 'True', arrest))
    df_filtered = filter_df(df_summ, year_list, ca, list_crimes, list_arrest)

    include_details = (list_crimes != [])

    metrics = calculate_metrics(df_filtered)

    return_list = [
        get_timeline(df_filtered, include_details),
        get_choropleth(df_filtered, ca, slider_option, year_list),
        get_bar_chart(df_filtered, slider_option, year_list)
    ] + metrics

    return return_list


# update map slider
@app.callback(
    [
        Output('slider-map','min'),
        Output('slider-map','max'),
        Output('slider-map','marks'),
        Output('slider-map','value')
    ],
    [Input('slider-years','value')]
)
def update_map_slider(year_list):
    marks = {
        year: str(year) if year_list[-1]-year_list[0] < 6 or n % 2 == 1 else ''
        for n, year in enumerate(range(year_list[0],year_list[-1]+1))
    }
    marks[year_list[0]-1] = 'Average'
    return (year_list[0]-1, year_list[-1], marks, year_list[0]-1)

  
@app.callback(
    Output('dropdown-crimes', 'value'),
    [Input('slider-top-crimes', 'value')]
)
def return_top_crimes(top):
    return df_summ.groupby('Primary Type')['Count'].sum().nlargest(top).index  



### RUN ###

if __name__ == '__main__':
    app.run_server(debug=True)
