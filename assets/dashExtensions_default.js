window.dashExtensions = Object.assign({}, window.dashExtensions, {
    default: {
        function0: function(feature, latlng, context) {

            var stationIcon = L.icon({
                iconUrl: 'assets/station.png',
                iconSize: [20, 20], // size of the icon
            });

            return L.marker(latlng, {
                icon: stationIcon
            })
        },
        function1: function(feature) {

            var geojsonMarkerOptions = {
                fillColor: "#4287f5",
                color: "#4287f5",
                weight: 1,
                opacity: 1,
                fillOpacity: 0.2
            };

            return geojsonMarkerOptions
        },
        function2: function(feature, layer, context) {
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
            `, {
                    direction: 'top',
                }
            )
        }
    }
});