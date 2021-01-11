import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objs as go


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = "Pie-chart"


server = app.server

df = pd.read_excel('Data.xlsx')


labels = ['Neutral', 'Positive', 'Negative']
d = dict(df['polarity'].value_counts())
#print(d)
#print(labels)
values = [d[i] for i in d]
#print(values)

fig = go.Figure(data=[go.Pie(labels=labels, values=values,)])

app = dash.Dash()
app.layout = html.Div([
    dcc.Graph(figure=fig)
])

app.run_server(debug=True)
