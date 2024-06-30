import dash_leaflet as dl
import dash_mantine_components as dmc
from dash import dcc, html, Input, Output, State, callback, clientside_callback, exceptions, no_update
from dash_iconify import DashIconify
import json
import numpy as np
from shapely.geometry import shape, Point, Polygon
from shapely.affinity import rotate
from pyproj import Transformer, CRS
from geojson import Feature, FeatureCollection, Point as GeoJsonPoint

import dash_leaflet as dl
from dash import Dash, html, Output, Input
from dash.exceptions import PreventUpdate
from dash_extensions.javascript import assign
from geojson import Feature, FeatureCollection, Point as GeoJsonPoint

boundary_options_enabled = [
    dcc.Upload(
        dmc.Button(
            'Upload .shp, .shx and .dbf file',
            radius='xl',
            variant='outline',
            color='orange',
            leftSection=DashIconify(icon='mdi:file-upload',width=20),
            n_clicks=0,
            size='xs',
            fullWidth=True
        ),
        id='upload',
        multiple=True,
    ),
    dmc.Flex(dmc.Text('or',size='sm'),justify='center'),
    dmc.SimpleGrid(
        [
            dmc.Button(
                'Create Rectangle',
                id='create_rectangle',
                radius='xl',
                variant='outline',
                leftSection=DashIconify(icon='ph:bounding-box-light',width=20),
                n_clicks=0,
                size='xs'
            ),
            dmc.Button(
                'Create Polygon',
                id='create_polygon',
                radius='xl',
                variant='outline',
                leftSection=DashIconify(icon='ph:polygon',width=20),
                n_clicks=0,
                size='xs',
                color='indigo'
            ),
        ],
        cols=2
    ),
]

boundary_options_disabled = [
    dmc.Button(
        'Delete Boundary',
        radius='xl',
        color='orange',
        leftSection=DashIconify(icon='ri:delete-bin-2-fill',width=20),
        n_clicks=0,
        size='xs',
        fullWidth=True,
        id='delete-boundary'
    )
]

input_boundary = dmc.Paper(
    dmc.Stack(
        [
            dmc.Group(
                [
                    DashIconify(icon='clarity:map-line',width=30),
                    dmc.Text('Boundaries',fw=500,size="lg"),
                ],
                gap=2
            ),
            dmc.Divider(),
            dmc.Stack(
                boundary_options_enabled,
                gap=0,
                pt=5,
                id='boundary_options'
            ),
        ],
        gap=5
    ),
    withBorder=True,
    p='lg',
    radius=0,
)

input_params = dmc.Paper(
    dmc.Stack(
        [
            dmc.Group(
                [
                    DashIconify(icon='carbon:parameter',width=30),
                    dmc.Text('Parameters',fw=500,size="lg"),
                ],
                gap=2
            ),
            dmc.Divider(),
            dmc.Grid(
                [
                    dmc.GridCol(
                        dmc.NumberInput(
                            label='Spacing',
                            id='spacing',
                            description='Space between points/stations'
                        ), 
                        span=7
                    ),
                    dmc.GridCol(
                        dmc.Flex(
                            dmc.RadioGroup(
                                children=dmc.Group([dmc.Radio(l,value=l,size='xs') for l in ['m','ft']],pt=8),
                                value='m',
                                pb=10
                            ),
                            align='flex-end',
                            h='100%'
                        ),
                        span=5,
                    ),
                ],
            ),
            dmc.Stack(
                [
                    dmc.Text('Orientation',fw=500,size="sm"),
                    dmc.Paper(
                        dmc.Grid(
                            [
                                dmc.GridCol(
                                    dmc.Slider(
                                        id="orientation",
                                        value=0,
                                        marks=[
                                            {"value": 45, "label": "45°"},
                                            {"value": 90, "label": "90°"},
                                            {"value": 135, "label": "135°"},
                                            {"value": 180, "label": "180°"},
                                        ],
                                        min=0,
                                        max=180,
                                        updatemode="drag",
                                        label=None,
                                    ),
                                    span='auto'
                                ),
                                dmc.GridCol(
                                    dmc.Text(
                                        id='orientation-value'
                                    ),
                                    span=2
                                )
                            ],
                            pb=10
                        ),
                        withBorder=True,
                        p='lg',
                        radius='sm'
                    )
                ],
                gap=2
            ),
            dmc.TextInput(
                label='Station Name Prefix',
                id='prefix',
                description='Name prefix for stations',
                value='STATION_',
            ), 
        ],
        gap=5
    ),
    withBorder=True,
    p='lg',
    radius=0,
)

button = dmc.Flex(
        dmc.Button(
            'Generate Stations',
            id='generate',
            color='green',
            leftSection=DashIconify(icon='mdi:gear',width=20),
            radius='xl',
            n_clicks=0
        ),
        justify='flex-end',
    )

draw_icon = assign("""
    function (feature, latlng, context) {
                   
        var stationIcon = L.icon({
            iconUrl: 'assets/station.png',
            iconSize: [20, 20], // size of the icon
        });
        
        return L.marker(latlng, {icon: stationIcon})
    }""")

boundary_style = assign("""
    function (feature) {
                   
        var geojsonMarkerOptions = {
            fillColor: "#4287f5",
            color: "#4287f5",
            weight: 1,
            opacity: 1,
            fillOpacity: 0.2
        };
                    
        return geojsonMarkerOptions
    }""")

on_each_feature = assign("""
    function(feature, layer, context){
        layer.bindTooltip(
            `<b>${feature.properties.station_name}</b>
            <table class=station_table>
            <tr>
                <th>Key</th>
                <th>Value</th>
            </tr>
            <tr>
                <td>Latitude</td>
                <td>${feature.geometry.coordinates[0]}</td>
            </tr>
            <tr>
                <td>Longitude</td>
                <td>${feature.geometry.coordinates[1]}</td>
            </tr>
            <tr>
                <td>Elevation</td>
                <td>${feature.properties.elevation}</td>
            </tr>
            </table> 
            `,
            {
                direction:'top',
            }
        )
}""")

map = dl.Map(center=[-2.600029, 118.015776], zoom=4, children=[
        dl.TileLayer(url='http://{s}.google.com/vt/lyrs=s,h&x={x}&y={y}&z={z}', maxZoom=20,subdomains=['mt0','mt1','mt2','mt3']), dl.FeatureGroup([
            dl.EditControl(id="edit_control")]), dl.GeoJSON(id="boundary", zoomToBounds=True, options=dict(style=boundary_style)),dl.GeoJSON(id="points", options=dict(pointToLayer=draw_icon), zoomToBounds=True, onEachFeature=on_each_feature), dl.ScaleControl(position="bottomleft")
    ], style={'height': '100vh','width':'70vw'}, id="map")


layout = dmc.Group(
    [
        dmc.Modal(
            id="loading",
            zIndex=10000,
            children=dmc.Center(
                [
                    dmc.Stack(
                        [
                            dmc.Loader(color="blue", size="xl", variant="oval"),
                            dmc.Text('Processing...')
                        ],
                        align='center'
                    ),
                ],
                id='output'
            ),
            closeButtonProps={'display':'none'},
            opened=False,
            centered=True
        ),
        dmc.Modal(
            id="error",
            zIndex=10000,
            children=dmc.Center(
                [
                    dmc.Stack(
                        [
                            DashIconify(icon='material-symbols:error',color='red',width=100),
                            dmc.Text('Sorry, an error occured. Try Again!')
                        ],
                        align='center'
                    )
                ],
                id='error-output'
            ),
            closeButtonProps={'display':'none'},
            opened=False,
            centered=True
        ),
        map,
        dmc.Stack(
            [
                input_boundary,
                input_params,
                button
            ],
            w='30vw',
        )
    ],
    gap=0
)

import requests


def estimate_utm_crs(lat, lon):

    utm_zone = int((lon + 180) // 6) + 1
    is_northern = lat >= 0
    return CRS.from_dict({
        'proj': 'utm',
        'zone': utm_zone,
        'north': is_northern
    })

def generate_grid_points(geojson_data, grid_spacing_meters, orientation_deg, prefix):

    polygon_geojson = shape(geojson_data['features'][0]['geometry'])
    polygon = Polygon(polygon_geojson)

    centroid = polygon.centroid
    crs_utm = estimate_utm_crs(centroid.y, centroid.x)
    
    crs_4326 = CRS("EPSG:4326")
    transformer_to_utm = Transformer.from_crs(crs_4326, crs_utm, always_xy=True)
    transformer_to_4326 = Transformer.from_crs(crs_utm, crs_4326, always_xy=True)

    polygon_utm_coords = [transformer_to_utm.transform(coord[0], coord[1]) for coord in polygon.exterior.coords]
    polygon_utm = Polygon(polygon_utm_coords)

    rotated_polygon_utm = rotate(polygon_utm, orientation_deg, origin=polygon_utm.centroid)
    min_x, min_y, max_x, max_y = rotated_polygon_utm.bounds

    x_coords = np.arange(min_x, max_x + grid_spacing_meters, grid_spacing_meters)
    y_coords = np.arange(min_y, max_y + grid_spacing_meters, grid_spacing_meters)
    grid_points = [Point(x, y) for x in x_coords for y in y_coords]

    centroid_utm = polygon_utm.centroid
    unrotated_points = [rotate(point, -orientation_deg, origin=centroid_utm) for point in grid_points]

    points_inside_polygon = [point for point in unrotated_points if polygon_utm.contains(point)]

    points_inside_polygon_4326 = [Point(transformer_to_4326.transform(point.x, point.y)) for point in points_inside_polygon]

    features = []

    url = "https://api.open-elevation.com/api/v1/lookup"
    locations = [{"latitude": point.y, "longitude": point.x} for point in points_inside_polygon_4326]
    response = requests.post(url, json={"locations": locations})
    elevations = []
    if response.status_code == 200:
        elevation_data = response.json()
        results = elevation_data['results']
        for i, coord in enumerate(points_inside_polygon_4326):
            elevations.append(results[i]['elevation'])
    else:
        raise Exception()

    for idx, point in enumerate(points_inside_polygon_4326):
        station_name = f'{prefix}{idx+1}'
        geojson_point = GeoJsonPoint((point.x, point.y))
        feature = Feature(geometry=geojson_point, properties={"station_name": station_name, 'elevation': f"{elevations[idx]} m"})
        features.append(feature)

    feature_collection = FeatureCollection(features)

    return feature_collection

import base64
import shapefile
import io
from shapely.geometry import shape, mapping

def base64_files_to_geojson(base64_shp, base64_shx, base64_dbf):
    # Decode the base64 encoded files
    decoded_shp = base64.b64decode(base64_shp)
    decoded_shx = base64.b64decode(base64_shx)
    decoded_dbf = base64.b64decode(base64_dbf)
    
    # Create in-memory file objects
    shp_io = io.BytesIO(decoded_shp)
    shx_io = io.BytesIO(decoded_shx)
    dbf_io = io.BytesIO(decoded_dbf)

    # Read the shapefile from in-memory file objects
    sf = shapefile.Reader(shp=shp_io, shx=shx_io, dbf=dbf_io)
    
    # Convert shapefile geometries to GeoJSON format
    geojson_features = []
    for sr in sf.shapeRecords():
        geom = shape(sr.shape.__geo_interface__)
        geojson_feature = {
            "type": "Feature",
            "geometry": mapping(geom),
            "properties": dict(zip([field[0] for field in sf.fields[1:]], sr.record))
        }
        geojson_features.append(geojson_feature)

    # Create GeoJSON structure
    geojson_dict = {
        "type": "FeatureCollection",
        "features": geojson_features
    }

    return geojson_dict

@callback(
    Output("boundary", "data",allow_duplicate=True),
    Input('upload', 'contents'),
    State('upload', 'filename'),
    prevent_initial_call=True
)
def update_output(contents, filenames):
    if contents is not None:
        base64_shp = base64_shx = base64_dbf = None
        for content, filename in zip(contents, filenames):
            content_type, content_string = content.split(',')
            if filename.endswith('.shp'):
                base64_shp = content_string
            elif filename.endswith('.shx'):
                base64_shx = content_string
            elif filename.endswith('.dbf'):
                base64_dbf = content_string

        if base64_shp and base64_shx and base64_dbf:

            geojson = base64_files_to_geojson(base64_shp, base64_shx, base64_dbf)

        return geojson
    
@callback(
    Output("points", "data",allow_duplicate=True),
    Output('loading','opened',allow_duplicate=True),
    Output('error-output','opened',allow_duplicate=True),
    Input('generate','n_clicks'),
    State("boundary", "data"),
    State('spacing','value'),
    State('orientation','value'),
    State('prefix','value'),
    prevent_initial_call=True)
def generate_points(n,current_geojson,y,z, prefix):
    if n>0:
        try:
            output = generate_grid_points(current_geojson,y,z,prefix)
            return output, False, False
        except:
            return no_update, False, True
    else:
        raise exceptions.PreventUpdate()

@callback(
    Output("boundary", "data", allow_duplicate=True),
    Output("boundary_options", "children", allow_duplicate=True),
    Input("delete-boundary", "n_clicks"),
    prevent_initial_call =True
)
def delete_boundary(n):
    if n>0:
        return dict(type= 'FeatureCollection', features= []), boundary_options_enabled
    else:
        raise exceptions.PreventUpdate()
    
@callback(
    Output("boundary_options", "children", allow_duplicate=True),
    Input("boundary", "data"),
    prevent_initial_call =True
)
def delete_boundary(x):

    if x is not None:

        if x['features']!=[]:

            return boundary_options_disabled

    raise exceptions.PreventUpdate()
        

clientside_callback(
    """
    function(n) {
        if (n>0) {
            return true
        }
    }
    """,
    Output('loading','opened'),
    Input('generate','n_clicks'),
)

clientside_callback(
    """
    function(orientation) {
        return `${orientation}°`
    }
    """,
    Output('orientation-value', 'children'),
    Input('orientation', 'value'),
)

clientside_callback(
    """
    function(n_clicks) {
        if (n_clicks > 0) {
            return {mode: "polygon", n_clicks: n_clicks};
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output("edit_control", "drawToolbar", allow_duplicate=True),
    Input("create_polygon", "n_clicks"),
    prevent_initial_call =True
)

clientside_callback(
    """
    function(n_clicks) {
        if (n_clicks > 0) {
            return {mode: "rectangle", n_clicks: n_clicks};
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output("edit_control", "drawToolbar", allow_duplicate=True),
    Input("create_rectangle", "n_clicks"),
    prevent_initial_call =True
)

clientside_callback(
    """
    function(x) {
        if (x.features.length !== 0) {
            return [x, {mode:"remove", action:"clear all",n_clicks:1}];
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output("boundary", "data"),
    Output("edit_control", "editToolbar"),
    Input("edit_control", "geojson"),
    prevent_initial_call=True
)



