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

choropleth_series = df_summ[df_summ['Year'] == 2019].groupby(['Community Area'])['Count'].sum()
data_choroplethmap = go.Choropleth(
    geojson=chicago_geojson,
    locations=choropleth_series.index,
    z=choropleth_series.values,
    colorscale='inferno',
    reversescale=True,
    colorbar=dict(title='Number of Crimes'),
    marker=dict(opacity=.85),
    zauto=False,
    zmin=0,
    zmax=max(choropleth_series.values)
)

layout_choroplethmap = go.Layout(
    mapbox=dict(
        style='white-bg',
        layers=[
            dict(
                source=feature,
                below='traces',
                type='fill',
                fill=dict(outlinecolor='white'))
            for feature in chicago_geojson['features']
        ]
    ),
    geo=dict(fitbounds='locations', visible=False)
)
    
app = dash.Dash(__name__)
server = app.server

app.layout = html.Div([
    dcc.Graph(figure=go.Figure(data=data_choroplethmap, layout=layout_choroplethmap))
])

if __name__ == '__main__':
    app.run_server(debug=True)
