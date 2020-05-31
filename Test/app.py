import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import pandas as pd
import numpy as np
import plotly.graph_objs as go
import json
from urllib.request import urlopen


# slider for map
slider_map = dcc.Slider(
    id='slider-map',
    min=2015,
    max=2017,
    step=1,
    marks={2015:'Average',2016:'Test',2017:'Test2'},
    value=0,
    included=False,
    updatemode='drag',
    vertical=True
)
    
app = dash.Dash(__name__)
server = app.server

app.layout = html.Div(slider_map)

if __name__ == '__main__':
    app.run_server(debug=True)
