import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import pandas as pd
import plotly.graph_objs as go
import settings
import mysql.connector
import datetime
import numpy as np

import re
import itertools
import nltk
nltk.download('punkt')
nltk.download('stopwords')
from nltk.probability import FreqDist
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from textblob import TextBlob


# connecting to database
mydb = mysql.connector.connect(host="localhost", user="root", passwd="<password>", database="<name of database>", charset="utf8")
query = "SELECT id_str, text, created_at, polarity, user_location, user_followers_count FROM {}".format(settings.TABLE_NAME)

# accessing database data
df = pd.read_sql(query, con=mydb)


# For pie-chart
labels = ['Neutral', 'Positive', 'Negative']
d = dict(df['polarity'].value_counts())
values = [d[i] for i in d]
fig = go.Figure(data=[go.Pie(labels=labels, values=values)])

# For Geographic chart (Chloropleth)
# Clean and transform data to enable word frequency
content = ' '.join(df["text"])
content = re.sub(r"http\S+", "", content)
content = content.replace('RT ', ' ').replace('&amp;', 'and')
content = re.sub('[^A-Za-z0-9]+', ' ', content)
content = content.lower()

# Filter constants for states in US
STATES = ['Alabama', 'AL', 'Alaska', 'AK', 'American Samoa', 'AS', 'Arizona', 'AZ', 'Arkansas', 'AR', 'California', 'CA', 'Colorado', 'CO', 'Connecticut', 'CT', 'Delaware', 'DE', 'District of Columbia', 'DC', 'Federated States of Micronesia', 'FM', 'Florida', 'FL', 'Georgia', 'GA', 'Guam', 'GU', 'Hawaii', 'HI', 'Idaho', 'ID', 'Illinois', 'IL', 'Indiana', 'IN', 'Iowa', 'IA', 'Kansas', 'KS', 'Kentucky', 'KY', 'Louisiana', 'LA', 'Maine', 'ME', 'Marshall Islands', 'MH', 'Maryland', 'MD', 'Massachusetts', 'MA', 'Michigan', 'MI', 'Minnesota', 'MN', 'Mississippi', 'MS', 'Missouri', 'MO', 'Montana', 'MT', 'Nebraska', 'NE', 'Nevada', 'NV', 'New Hampshire', 'NH', 'New Jersey', 'NJ', 'New Mexico', 'NM', 'New York', 'NY', 'North Carolina', 'NC', 'North Dakota', 'ND', 'Northern Mariana Islands', 'MP', 'Ohio', 'OH', 'Oklahoma', 'OK', 'Oregon', 'OR', 'Palau', 'PW', 'Pennsylvania', 'PA', 'Puerto Rico', 'PR', 'Rhode Island', 'RI', 'South Carolina', 'SC', 'South Dakota', 'SD', 'Tennessee', 'TN', 'Texas', 'TX', 'Utah', 'UT', 'Vermont', 'VT', 'Virgin Islands', 'VI', 'Virginia', 'VA', 'Washington', 'WA', 'West Virginia', 'WV', 'Wisconsin', 'WI', 'Wyoming', 'WY']
STATE_DICT = dict(itertools.zip_longest(*[iter(STATES)] * 2, fillvalue=""))
INV_STATE_DICT = dict((v,k) for k,v in STATE_DICT.items())

# Clean and transform data to enable geo-distribution
is_in_US=[]
geo = df[['user_location']]
df = df.fillna(" ")
for x in df['user_location']:
    check = False
    for s in STATES:
        if s in x:
            is_in_US.append(STATE_DICT[s] if s in STATE_DICT else s)
            check = True
            break
    if not check:
        is_in_US.append(None)

geo_dist = pd.DataFrame(is_in_US, columns=['State']).dropna().reset_index()
geo_dist = geo_dist.groupby('State').count().rename(columns={"index": "Number"}) \
    .sort_values(by=['Number'], ascending=False).reset_index()
geo_dist["Log Num"] = geo_dist["Number"].apply(lambda x: np.log2(x))


geo_dist['Full State Name'] = geo_dist['State'].apply(lambda x: INV_STATE_DICT[x])
geo_dist['text'] = geo_dist['Full State Name'] + '<br>' + 'Num: ' + geo_dist['Number'].astype(str)


tokenized_word = word_tokenize(content)
stop_words=set(stopwords.words("english"))
filtered_sent=[]
for w in tokenized_word:
    if (w not in stop_words) and (len(w) >= 3):
        filtered_sent.append(w)
fdist = FreqDist(filtered_sent)
fd = pd.DataFrame(fdist.most_common(16), columns = ["Word","Frequency"]).drop([0]).reindex()
fd['Polarity'] = fd['Word'].apply(lambda x: TextBlob(x).sentiment.polarity)
fd['Marker_Color'] = fd['Polarity'].apply(lambda x: 'rgba(255, 50, 50, 0.6)' if x < -0.1 else \
    ('rgba(184, 247, 212, 0.6)' if x > 0.1 else 'rgba(131, 90, 241, 0.6)'))
fd['Line_Color'] = fd['Polarity'].apply(lambda x: 'rgba(255, 50, 50, 1)' if x < -0.1 else \
    ('rgba(184, 247, 212, 1)' if x > 0.1 else 'rgba(131, 90, 241, 1)'))

geo = go.Figure(
    go.Choropleth(
                                    locations=geo_dist['State'], # Spatial coordinates
                                    z = geo_dist['Log Num'].astype(float), # Data to be color-coded
                                    locationmode = 'USA-states', # set of locations match entries in `locations`
                                    #colorscale = "Blues",
                                    text=geo_dist['text'], # hover text
                                    geo = 'geo',
                                    colorbar_title = "Num in Log2",
                                    marker_line_color='white',
                                    colorscale = ["#fdf7ff", "#835af1"],
                                    #autocolorscale=False,
                                    #reversescale=True,
                                ) 
)


## Application
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = "Sentiment Analysis on COVID-19 Tweets"
server = app.server
app.layout = html.Div(children=[
    html.H2('Real-time Twitter Sentiment Analysis for COVID-19 ', style={
        'textAlign': 'center'
    }),
    html.H4('(Last updated: July 14, 2020)', style={
        'textAlign': 'right'
    }),

    html.Div([
    dash_table.DataTable(
    id='table',
    columns=[{"name": i, "id": i} for i in df.columns],
    data=df.to_dict('records'),
    export_format='xlsx',
    export_headers='display',
    merge_duplicate_headers=True,
    page_current=0,
    page_size=10
    )]),


    html.Div(dcc.Graph(figure=fig)), 
    html.Div(dcc.Graph(figure=geo)),
    
    # Author's Words
    html.Div(
        className='row',
        children=[ 
            dcc.Markdown("__Contributor's Words__: This application was previously used for IBM Hack Challenge 2020. A modified version is being submitted for MLH's Local Hack Day 2021 Day 2's Leverage Sentiment Analysis Challenge!"),
        ],style={'width': '35%', 'marginLeft': 70}
    ),
    html.Br(),
    
    # ABOUT ROW
    html.Div(
        className='row',
        children=[
            html.Div(
                className='three columns',
                children=[
                    html.P(
                    'Data extracted from:'
                    ),
                    html.A(
                        'Twitter API',
                        href='https://developer.twitter.com'
                    )                    
                ]
            ),
            html.Div(
                className='three columns',
                children=[
                    html.P(
                    'Code avaliable at:'
                    ),
                    html.A(
                        'GitHub',
                        href='https://github.com/NehaKoppikar/Leverage_Sentiment_Analysis'
                    )                    
                ]
            ),
            html.Div(
                className='three columns',
                children=[
                    html.P(
                    'Made with:'
                    ),
                    html.A(
                        'Dash / Plot.ly',
                        href='https://plot.ly/dash/'
                    )                    
                ]
            ),
            html.Div(
                className='three columns',
                children=[
                    html.P(
                    'Contributors:'
                    ),
                    html.A(
                        'Neha Koppikar',
                        href='https://www.linkedin.com/in/neha-koppikar-a8a56314b/'
                        href="https://twitter.com/koppikar_neha"
                    )
                ]
            ),                                               
        ], style={'marginLeft': 70, 'fontSize': 16}
    ),

    ],style={'padding': '20px'}) 


if __name__ == '__main__':
    app.run_server(debug=True)
