#https://dash.plot.ly/live-updates

import datetime, csv, math

import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly
from dash.dependencies import Input, Output, State

# pip install pyorbital
from pyorbital.orbital import Orbital
#satellite = Orbital('TERRA')

from mqtt_monitor_silent import mqtt_feed
mqttc = mqtt_feed()

import config

#######DATA

center = config.center
zoom = config.zoom

#Markers
map_data = [
    {#000
        "type": "scattermapbox",
        "lat": [center['lat']+0.0000],
        "lon": [center['lon']],
        "hoverinfo": "text+lon+lat",
        "text": "000",
        "code": "000",
        "mode": "markers",
        "marker": {"size": 1, "color": "green"},
    },
    {#001
        "type": "scattermapbox",
        "lat": [center['lat']+0.0001],
        "lon": [center['lon']],
        "hoverinfo": "text+lon+lat",
        "text": "001",
        "code": "001",
        "mode": "markers",
        "marker": {"size": 15, "color": "green"},
    },
    {#002
        "type": "scattermapbox",
        "lat": [center['lat']+0.0002],
        "lon": [center['lon']],
        "hoverinfo": "text+lon+lat",
        "text": "002",
        "code": "001",
        "mode": "markers",
        "marker": {"size": 15, "color": "green"},
    },
    {#003
        "type": "scattermapbox",
        "lat": [center['lat']+0.0003],
        "lon": [center['lon']],
        "hoverinfo": "text+lon+lat",
        "text": "003",
        "code": "001",
        "mode": "markers",
        "marker": {"size": 1, "color": "green"},
    },
    {#004
        "type": "scattermapbox",
        "lat": [center['lat']+0.0004],
        "lon": [center['lon']],
        "hoverinfo": "text+lon+lat",
        "text": "004",
        "code": "001",
        "mode": "markers",
        "marker": {"size": 15, "color": "green"},
    },
    {#005
        "type": "scattermapbox",
        "lat": [center['lat']+0.0005],
        "lon": [center['lon']],
        "hoverinfo": "text+lon+lat",
        "text": "005",
        "code": "001",
        "mode": "markers",
        "marker": {"size": 1, "color": "green"},
    },
    {#006
        "type": "scattermapbox",
        "lat": [center['lat']+0.0006],
        "lon": [center['lon']],
        "hoverinfo": "text+lon+lat",
        "text": "006",
        "code": "001",
        "mode": "markers",
        "marker": {"size": 15, "color": "green"},
    },
    {#007
        "type": "scattermapbox",
        "lat": [center['lat']+0.0007],
        "lon": [center['lon']],
        "hoverinfo": "text+lon+lat",
        "text": "007",
        "code": "001",
        "mode": "markers",
        "marker": {"size": 15, "color": "green"},
    },
    {#008
        "type": "scattermapbox",
        "lat": [center['lat']+0.0008],
        "lon": [center['lon']],
        "hoverinfo": "text+lon+lat",
        "text": "008",
        "code": "001",
        "mode": "markers",
        "marker": {"size": 15, "color": "green"},
    },
    {
        "type": "scattermapbox",
        "lat": [center['lat']+0.0009],
        "lon": [center['lon']],
        "hoverinfo": "text+lon+lat",
        "text": "009",
        "code": "001",
        "mode": "markers",
        "marker": {"size": 15, "color": "green"},
    },
    {
        "type": "scattermapbox",
        "lat": [center['lat']+0.0010],
        "lon": [center['lon']],
        "hoverinfo": "text+lon+lat",
        "text": "010",
        "code": "001",
        "mode": "markers",
        "marker": {"size":15, "color": "green"},
    },
]

featuresList = []
for polygon in mqttc.geofence.coordsArray:
    featuresList.append({'type': "Feature",'geometry': {'type': "MultiPolygon",'coordinates': [[polygon]]}})

map_layout = {
    "mapbox": {
        "style": "open-street-map",
        "center": center,
        "zoom":zoom,
        'layers': [{
            'source': {
                'type': "FeatureCollection",
                'features': featuresList
            },
            'type': "fill",
            'below': "traces",
            'color': "green",
            'opacity':0.15,
        }],
    },
    "showlegend": False,
    "autosize": True,
    "paper_bgcolor": "#1e1e1e",
    "plot_bgcolor": "#1e1e1e",
    "margin": {"t": 0, "r": 0, "b": 0, "l": 0},
}



external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.layout = html.Div(
    html.Div([
        html.H4('Fleet Monitor Live Feed'),


		html.H2(id = 'timestamp-text',style={'opacity': '1','color': 'black', 'fontSize': 15}),
        html.Br([]),

        html.Div(id='live-update-text'),


        dcc.Graph(
            id='world-map',
            style={
                'height': 600,
            },
            figure={"data": map_data, "layout": map_layout},
            config={"displayModeBar": True, "scrollZoom": True}
        ),

        dcc.Store(id='store-data',
            data={
                'started' : False,
                'bike_dict' : None
            }

        ),
        dcc.Interval(
            id='interval-component',
            interval=1*1000, # in milliseconds
            n_intervals=0
        )
    ],
        style={'background-image': 'url("/assets/logo.png")',
            'background-position': 'right top',
            'background-repeat': 'no-repeat',
            'background-size': '50%'
        }
    )
)





@app.callback(Output('timestamp-text', 'children'),
              [Input('interval-component', 'n_intervals')])
def update_timestamp(n):
	return datetime.datetime.now().strftime('%Y-%m-%d   %H:%M:%S')




@app.callback(
                Output('world-map', 'figure'),
                [Input('interval-component', 'n_intervals')],
                [State("world-map", "figure"),
                State('store-data', 'data')]
              )
def update_maps(n,old_figure,data):
    fig = old_figure
    #fig["data"][1]['lat'][0] -= 0.00009
    newFeatures = []
    for polygon in mqttc.monitor.geofence.coordsArray:
        newFeatures.append({'type': "Feature",'geometry': {'type': "MultiPolygon",'coordinates': [[polygon]]}})
    fig["layout"]["mapbox"]["layers"][0]["source"]["features"] = newFeatures

    for key, (tdict, ts) in sorted(mqttc.monitor.bike_dict.items()):
        #If there is a value, map marker will update
        if '000' in tdict['name']:
            if not math.isnan(tdict['lat']):
                fig["data"][0]['lat'][0] = tdict['lat']
            if not math.isnan(tdict['long']):
                fig["data"][0]['lon'][0] = tdict['long']
        elif '001' in tdict['name']:
            if not math.isnan(tdict['lat']):
                fig["data"][1]['lat'][0] = tdict['lat']
            if not math.isnan(tdict['long']):
                fig["data"][1]['lon'][0] = tdict['long']
        elif '002' in tdict['name']:
            if not math.isnan(tdict['lat']):
                fig["data"][2]['lat'][0] = tdict['lat']
            if not math.isnan(tdict['long']):
                fig["data"][2]['lon'][0] = tdict['long']
        elif '003' in tdict['name']:
            if not math.isnan(tdict['lat']):
                fig["data"][3]['lat'][0] = tdict['lat']
            if not math.isnan(tdict['long']):
                fig["data"][3]['lon'][0] = tdict['long']
        elif '004' in tdict['name']:
            if not math.isnan(tdict['lat']):
                fig["data"][4]['lat'][0] = tdict['lat']
            if not math.isnan(tdict['long']):
                fig["data"][4]['lon'][0] = tdict['long']
        elif '005' in tdict['name']:
            if not math.isnan(tdict['lat']):
                fig["data"][5]['lat'][0] = tdict['lat']
            if not math.isnan(tdict['long']):
                fig["data"][5]['lon'][0] = tdict['long']
        elif '006' in tdict['name']:
            if not math.isnan(tdict['lat']):
                fig["data"][6]['lat'][0] = tdict['lat']
            if not math.isnan(tdict['long']):
                fig["data"][6]['lon'][0] = tdict['long']
        elif '007' in tdict['name']:
            if not math.isnan(tdict['lat']):
                fig["data"][7]['lat'][0] = tdict['lat']
            if not math.isnan(tdict['long']):
                fig["data"][7]['lon'][0] = tdict['long']
        elif '008' in tdict['name']:
            if not math.isnan(tdict['lat']):
                fig["data"][8]['lat'][0] = tdict['lat']
            if not math.isnan(tdict['long']):
                fig["data"][8]['lon'][0] = tdict['long']
        elif '009' in tdict['name']:
            if not math.isnan(tdict['lat']):
                fig["data"][9]['lat'][0] = tdict['lat']
            if not math.isnan(tdict['long']):
                fig["data"][9]['lon'][0] = tdict['long']
        elif '010' in tdict['name']:
            if not math.isnan(tdict['lat']):
                fig["data"][10]['lat'][0] = tdict['lat']
            if not math.isnan(tdict['long']):
                fig["data"][10]['lon'][0] = tdict['long']

    if data['started']:
        print('Ready')
    return fig


itemlist = ['name', 'lat', 'long', 'lock_status', 'message','Temperature','IAQ','Humidity','Pressure','Altitude']

@app.callback(Output('store-data', 'data'),
              [Input('interval-component', 'n_intervals')],
              [State('store-data', 'data')],
              )
def update_data(n, data):

    if n is None:
        os.system('clear')
        print('N :', n, end = '\n'*10)
        mqttc.start()

        if data['started'] is False:
            data['started'] = True
            #data['mqttc'] = mqttc


        else:
            #update function here
            pass
    data['bike_dict'] = mqttc.monitor.bike_dict
    return data



#Table

Titles = ['Device Code', 'Latitude', 'Longitude', 'Lock Status', 'message','Temperature','IAQ','Humidity','Pressure','Altitude (P based)']

@app.callback(
                Output('live-update-text', 'children'),
                [Input('interval-component', 'n_intervals')],
                [State('store-data', 'data')]
              )
def update_metrics(n,data):
    #print('tempt_dict\n'*20)
    table_dict = {}
    try:
        for key, value in iter(sorted(mqttc.monitor.bike_dict.items())):
            tdict, ts = value

            """print(ts)
            print(ts)
            print(ts)
            print(ts)
            print(ts)
            print(key, tdict)"""


            for key2 in itemlist:
                #IF no data
                if key2 not in tdict: #create an entry and blank data
                    tdict[key2] = ' '
                if key2 == 'lock_status':
                    if tdict['lock_status'].upper() == 'D':
                        tdict['lock_status'] = 'Restarted'

                    elif tdict['lock_status'].upper() == 'U':
                        tdict['lock_status'] = 'Unlocked'
                    elif tdict['lock_status'].upper() == 'L':
                        tdict['lock_status'] = 'Locked'
                    else:
                        pass
            pass
            table_dict[key] = tdict


        return html.Table(
            # Header
            [html.Tr([html.Th(col) for col in Titles])] +

            # Body
            [html.Tr([
                html.Td(str(tdict[v])) if v != 'name' else html.Td(tdict[v].replace('UPD-','')) for v in itemlist])

    		for key, tdict in table_dict.items()
    		]
        )
    except Exception as e:
        print('exception\n'*50)
        print(e)
        print('exception\n'*50)

        pass






if __name__ == '__main__':
    app.run_server(debug=False, host ='0.0.0.0')
