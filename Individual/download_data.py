import settings
import credentials

import mysql.connector

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_table

import pandas as pd
#import flask
#import io

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = "Download data"


server = app.server

conn = mysql.connector.connect(host="localhost", user="root", passwd="pwd", database="TwitterDB", charset="utf8")
query = "SELECT id_str, text, created_at, polarity, user_location, user_followers_count FROM {}".format(settings.TABLE_NAME)
df = pd.read_sql(query, con=conn)
df[' index'] = range(1, len(df) + 1)

app.layout = html.Div([
    dash_table.DataTable(
    id='table',
    columns=[{"name": i, "id": i} for i in df.columns],
    data=df.to_dict('records'),
    export_format='xlsx',
    export_headers='display',
    merge_duplicate_headers=True
    ),

])


if __name__ == '__main__':
    app.run_server(debug=True)
