import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.graph_objs as go


app =  dash.Dash()

app.layouyt = html.Div([
    'Test'
])


if __name__ == '__main__':
    app.run_server(debug=True)