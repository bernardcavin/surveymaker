import dash_leaflet as dl
import dash_mantine_components as dmc
from dash import dcc, html, Input, Output, State, callback, clientside_callback, exceptions, no_update
from dash_iconify import DashIconify
import numpy as np
from shapely.geometry import shape, Point, Polygon
from shapely.affinity import rotate
from pyproj import Transformer, CRS
from geojson import Feature, FeatureCollection, Point as GeoJsonPoint
from dash_extensions.javascript import assign
import requests

credit = dmc.Paper(
    dmc.Group(
        [
            dmc.Group(
                [
                    dmc.ThemeIcon(
                        size="lg",
                        color="indigo",
                        variant="outline",
                        radius='xl',
                        children=DashIconify(
                            icon='arcticons:networksurvey',width=20
                        ),
                    ),
                    dmc.Text('Survey Planner v0.01',size='md',fw=200),
                ],
                gap='sm'
            ),
            dmc.AvatarGroup(
                [
                    html.A(
                        dmc.Tooltip(
                            dmc.Avatar(
                                src="assets/bernard.jpeg",
                                size="md",
                                radius="xl",
                            ),
                            label="Bernard Cavin Ronlei",
                            position="bottom",
                        ),
                        href="https://www.linkedin.com/in/bangber/",
                        target="_blank",
                    ),
                    html.A(
                        dmc.Tooltip(
                            dmc.Avatar(
                                src="assets/junita.jpg",
                                size="md",
                                radius="xl",
                            ),
                            label="Junita Cintia Dewi Br. Pinem",
                            position="bottom",
                        ),
                        href="https://www.linkedin.com/in/junita-cintia-dewi-br-pinem-127404265/",
                        target="_blank",
                    )
                ]
            ),
        ],
        justify='space-between',
    ),
    withBorder=True,
    p='xs',
    radius='md',
    w=350
)

results = dmc.Paper(
    dmc.Stack(
        [
            dmc.Group(
                [
                    DashIconify(icon='carbon:result',width=30),
                    dmc.Text('Results',fw=500,size="lg"),
                ],
                gap=2
            ),
            dmc.Divider(),
            dmc.Group(
                [
                    dmc.Text('Approximate area : ',fw=500,size='sm'),
                    dmc.Text(id='result-area',size='sm')
                ],
                gap=5
            ),
            dmc.Group(
                [
                    dmc.Text('Number of Points : ',fw=500,size='sm'),
                    dmc.Text(id='result-points',size='sm')
                ],
                gap=5
            ),
            dmc.Group(
                [
                    dmc.Text('Average Elevation : ',fw=500,size='sm'),
                    dmc.Text(id='result-avg-elevation',size='sm')
                ],
                gap=5
            ),
            dmc.Group(
                [
                    dmc.Text('Maximum Elevation : ',fw=500,size='sm'),
                    dmc.Text(id='result-max-elevation',size='sm')
                ],
                gap=5
            ),
            dmc.Group(
                [
                    dmc.Text('Minimum Elevation : ',fw=500,size='sm'),
                    dmc.Text(id='result-min-elevation',size='sm')
                ],
                gap=5
            ),
            dmc.SimpleGrid(
                [
                    dmc.Button(
                        'Clear',
                        id='clear',
                        radius='xl',
                        color='green',
                        variant='outline',
                        leftSection=DashIconify(icon='ant-design:clear-outlined',width=20),
                        n_clicks=0,
                        size='xs',
                        h=50
                    ),
                    dmc.Button(
                        'Download .csv',
                        id='download',
                        radius='xl',
                        variant='outline',
                        leftSection=DashIconify(icon='ph:file-csv-light',width=20),
                        n_clicks=0,
                        size='xs',
                        color='blue',
                        h=50
                    ),
                ],
                cols=2
            ),
        ],
        gap='sm'
    ),
    withBorder=True,
    p='lg',
    radius='md',
    w=350
)


boundary_options_enabled = [
    dmc.SimpleGrid(
        [
            dmc.Button(
                'Create Rectangle',
                id='create_rectangle',
                radius='xl',
                variant='outline',
                leftSection=DashIconify(icon='ph:bounding-box-light',width=20),
                n_clicks=0,
                size='xs',
                h=50
            ),
            dmc.Button(
                'Create Polygon',
                id='create_polygon',
                radius='xl',
                variant='outline',
                leftSection=DashIconify(icon='ph:polygon',width=20),
                n_clicks=0,
                size='xs',
                color='indigo',
                h=50
            ),
        ],
        cols=2
    ),
]

boundary_options_cancel = dmc.Stack(
    [
        dmc.Button(
            'Cancel',
            id='cancel',
            radius='xl',
            variant='outline',
            leftSection=DashIconify(icon='material-symbols:cancel',width=20),
            n_clicks=0,
            size='xs',
            h=50,
            color='orange'
        ),
        dmc.Text('Draw boundary on the map')
    ]
)

boundary_options_disabled = [
    dmc.Button(
        'Delete Boundary',
        radius='xl',
        color='red',
        leftSection=DashIconify(icon='ri:delete-bin-2-fill',width=20),
        n_clicks=0,
        size='xs',
        fullWidth=True,
        id='delete-boundary',
        h=50
    )
]

input_boundary = dmc.Paper(
    dmc.Stack(
        [
            dmc.Group(
                [
                    DashIconify(icon='clarity:map-line',width=30),
                    dmc.Text('Boundary',fw=500,size="lg"),
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
            dmc.Group(
                [
                    dmc.Text('Approximate area : ',fw=500,size='sm'),
                    dmc.Text(id='area',size='sm')
                ],
                justify='left',
                display='none',
                id='area-container',
                gap=0
            )
        ],
        gap='sm'
    ),
    withBorder=True,
    p='lg',
    radius='md',
    w=350
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
                                pt=45,
                                id='unit'
                            ),
                            align='flex-start',
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
    radius='md',
    w=350
)

button = dmc.Flex(
    dmc.Button(
        'Generate Stations',
        id='generate',
        color='green',
        leftSection=DashIconify(icon='mdi:gear',width=20),
        radius='xl',
        n_clicks=0,
        h=50
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

map = dl.Map(center=[-2.600029, 118.015776], attributionControl=False,zoom=4, children=[
        dl.TileLayer(url='http://{s}.google.com/vt/lyrs=s,h&x={x}&y={y}&z={z}', maxZoom=20,subdomains=['mt0','mt1','mt2','mt3']), dl.FeatureGroup([
            dl.EditControl(id="edit_control")]), dl.GeoJSON(id="boundary", zoomToBounds=True, options=dict(style=boundary_style)),dl.GeoJSON(id="points", options=dict(pointToLayer=draw_icon), onEachFeature=on_each_feature), dl.ScaleControl(position="bottomleft")
    ], style={'height': '100vh','width':'100vw'}, id="map")


layout = dmc.Group(
    [
        dcc.Download(id="download-data"),
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
            centered=True,
            closeOnClickOutside=False
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
        dmc.Affix(
            dmc.Stack(
                [
                    credit,
                    dmc.Stack(
                        [
                            input_boundary,
                            dmc.Stack(
                                [
                                    input_params,
                                    button
                                    
                                ],
                                id='params',
                                display='none'
                            ),
                        ],
                        id='input-params'
                    ),
                    dmc.Group(
                        results,
                        display='none',
                        id='result-container'
                    )
                ],
            ),
            position={'top':20,'right':20},
            zIndex=1000,
            style={'zoom':'85%'}
        ),
    ],
    gap=0,
)

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
        for i, point in enumerate(points_inside_polygon):
            elevations.append(results[i]['elevation'])
    else:
        raise Exception("Failed to retrieve elevation data")

    params = crs_utm.to_string().split()
    projection = {}

    for param in params:
        if '=' in param:
            key, value = param.split('=')
            projection[key] = value

    utm_zone_letter = 'N' if centroid.y >= 0 else 'S'
    utm_zone = f"{projection.get('+zone')}{utm_zone_letter}"

    for idx, point in enumerate(points_inside_polygon):
        lat_lon_point = points_inside_polygon_4326[idx]
        station_name = f'{prefix}{idx+1}'
        utm_x, utm_y = point.x, point.y
        if utm_y < 0:
            utm_y += 10000000  # Add 10,000,000 meters to ensure positive value in southern hemisphere

        geojson_point = GeoJsonPoint((lat_lon_point.x, lat_lon_point.y))
        feature = Feature(geometry=geojson_point, properties={
            "station_name": station_name,
            "latitude": lat_lon_point.y,
            "longitude": lat_lon_point.x,
            "utm_x": utm_x,
            "utm_y": utm_y,
            "utm_zone": utm_zone,
            'elevation': elevations[idx]
        })
        features.append(feature)

    feature_collection = FeatureCollection(features)

    num_points = len(points_inside_polygon_4326)
    avg_elevation = sum(elevations) / num_points
    max_elevation = max(elevations)
    min_elevation = min(elevations)
    
    avg_elevation = f"{avg_elevation:.2f} m"
    max_elevation = f"{max_elevation} m"
    min_elevation = f"{min_elevation} m"

    return feature_collection, num_points, avg_elevation, max_elevation, min_elevation



@callback(
    Output("points", "data",allow_duplicate=True),
    Output('loading','opened',allow_duplicate=True),
    Output('error-output','opened',allow_duplicate=True),
    Output('spacing','error', allow_duplicate=True),
    Output('result-area','children', allow_duplicate=True),
    Output('result-points','children', allow_duplicate=True),
    Output('result-avg-elevation','children', allow_duplicate=True),
    Output('result-max-elevation','children', allow_duplicate=True),
    Output('result-min-elevation','children', allow_duplicate=True),
    Output('input-params','display', allow_duplicate=True),
    Output('result-container','display', allow_duplicate=True),
    Input('generate','n_clicks'),
    State("boundary", "data"),
    State('spacing','value'),
    State("unit",'value'),
    State('orientation','value'),
    State('prefix','value'),
    State('area','children'),
    prevent_initial_call=True)
def generate_points(n,current_geojson,spacing,unit,orientation, prefix, area):
    if n>0:
        if spacing in ['',None]:
            return no_update, no_update, no_update, 'Spacing cannot be empty', no_update, no_update, no_update, no_update, no_update, no_update, no_update
        try:
            if unit == 'ft':
                spacing = spacing*0.3048
            elif unit =='m':
                pass
            output, num_points, avg_elevation, max_elevation, min_elevation  = generate_grid_points(current_geojson,spacing,orientation,prefix)
            return output, False, False, no_update, area, num_points, avg_elevation, max_elevation, min_elevation, 'none', None
        except:
            return no_update, False, True, no_update
    else:
        raise exceptions.PreventUpdate()

@callback(
    Output("boundary", "data", allow_duplicate=True),
    Output("boundary_options", "children", allow_duplicate=True),
    Output('area-container','display', allow_duplicate=True),
    Output('params','display', allow_duplicate=True),
    Input("delete-boundary", "n_clicks"),
    prevent_initial_call =True
)
def delete_boundary(n):
    if n>0:
        return dict(type= 'FeatureCollection', features= []), boundary_options_enabled, 'none', 'none'
    else:
        raise exceptions.PreventUpdate()

@callback(
    Output("boundary", "data", allow_duplicate=True),
    Output("points", "data", allow_duplicate=True),
    Output("boundary_options", "children", allow_duplicate=True),
    Output('area-container','display', allow_duplicate=True),
    Output('params','display', allow_duplicate=True),
    Output('input-params','display', allow_duplicate=True),
    Output('result-container','display', allow_duplicate=True),
    Input("clear", "n_clicks"),
    prevent_initial_call =True
)
def delete_boundary(n):
    if n>0:
        return dict(type= 'FeatureCollection', features= []),dict(type= 'FeatureCollection', features= []), boundary_options_enabled, 'none', 'none', None, 'none'
    else:
        raise exceptions.PreventUpdate()
    
@callback(
    Output("boundary_options", "children", allow_duplicate=True),
    Output('area-container','display', allow_duplicate=True),
    Output('params','display', allow_duplicate=True),
    Input("boundary", "data"),
    prevent_initial_call =True
)
def show_delete_boundary(x):

    if x is not None:

        if x['features']!=[]:

            return boundary_options_disabled, 'inline', None

    raise exceptions.PreventUpdate()

clientside_callback(
    """
    function(n_clicks, geojson) {
        if (n_clicks > 0) {
            const rows = geojson.features.map(feature => ({
                station_name: feature.properties.station_name,
                latitude: feature.geometry.coordinates[1],
                longitude: feature.geometry.coordinates[0],
                utm_x: feature.properties.utm_x,
                utm_y: feature.properties.utm_y,
                utm_zone: feature.properties.utm_zone,
                elevation: feature.properties.elevation
            }));

            const csvContent = "data:text/csv;charset=utf-8,"
                + ['station_name,latitude,longitude,utm_x,utm_y,utm_zone,elevation']
                .concat(rows.map(row => `${row.station_name},${row.latitude},${row.longitude},${row.utm_x},${row.utm_y},${row.utm_zone},${row.elevation}`))
                .join("\\n");

            const encodedUri = encodeURI(csvContent);
            const link = document.createElement("a");
            link.setAttribute("href", encodedUri);
            link.setAttribute("download", "points.csv");
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
    }
    """,
    Output('download-data', 'data'),
    Input('download', 'n_clicks'),
    State('points', 'data')
)

clientside_callback(
    """
    function(n,spacing) {
        if (n>0) {
            if (!['',null,undefined].includes(spacing)) {
                console.log(spacing);
                return true
            }
        }
    }
    """,
    Output('loading','opened'),
    Input('generate','n_clicks'),
    State('spacing','value')
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

@callback(
    Output("edit_control", "drawToolbar", allow_duplicate=True),
    Output("boundary_options", "children", allow_duplicate=True),
    Input("cancel", "n_clicks"),
    prevent_initial_call=True
)
def update_draw_toolbar(n):
    if n > 0 :
        return {"action": "cancel","mode": "polygon", "n_clicks": n}, boundary_options_enabled
    return no_update

@callback(
    Output("edit_control", "drawToolbar", allow_duplicate=True),
    Output("boundary_options", "children", allow_duplicate=True),
    Input("create_polygon", "n_clicks"),
    prevent_initial_call=True
)
def update_draw_toolbar_polygon(n):
    if n:
        return {"mode": "polygon", "n_clicks": n}, boundary_options_cancel
    return no_update

@callback(
    Output("edit_control", "drawToolbar", allow_duplicate=True),
    Output("boundary_options", "children", allow_duplicate=True),
    Input("create_rectangle", "n_clicks"),
    prevent_initial_call=True
)
def update_draw_toolbar_rectangle(n):
    if n:
        return {"mode": "rectangle", "n_clicks": n}, boundary_options_cancel
    return no_update

clientside_callback(
    """
    function(x) {
        if (x.features.length !== 0) {
            var area = 0;
            var R = 6371000; // Earth radius in meters
            x.features.forEach(function(feature) {
                if (feature.geometry.type === "Polygon") {
                    var coordinates = feature.geometry.coordinates[0];
                    for (var i = 0, j = coordinates.length - 1; i < coordinates.length; j = i++) {
                        var lat1 = coordinates[i][1] * Math.PI / 180;
                        var lat2 = coordinates[j][1] * Math.PI / 180;
                        var lon1 = coordinates[i][0] * Math.PI / 180;
                        var lon2 = coordinates[j][0] * Math.PI / 180;
                        area += (lon2 - lon1) * (2 + Math.sin(lat1) + Math.sin(lat2));
                    }
                    area = Math.abs(area * R * R / 2);
                }
            });
            var cubicMeters = area;
            var formattedArea = cubicMeters.toFixed(2).replace(/\\B(?=(\\d{3})+(?!\\d))/g, ",") + " m²";
            return [x, {mode:"remove", action:"clear all", n_clicks:1}, formattedArea, 'inline'];
        }
        return [window.dash_clientside.no_update, window.dash_clientside.no_update, window.dash_clientside.no_update, window.dash_clientside.no_update];
    }
    """,
    Output("boundary", "data"),
    Output("edit_control", "editToolbar"),
    Output("area", "children"),
    Output("area-container", "display"),
    Input("edit_control", "geojson"),
    prevent_initial_call=True
)






