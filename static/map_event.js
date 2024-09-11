document.addEventListener("DOMContentLoaded", function() {
    // Initialize the Leaflet map
    var map = window.L.map('mapid').setView([0, 0], 3);

    // Add a tile layer to the map
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19
    }).addTo(map);

    // Drawing controls
    var drawnItems = new L.FeatureGroup();
    map.addLayer(drawnItems);

    var drawControl = new L.Control.Draw({
        draw: {
            polyline: false,
            polygon: false,
            circle: false,
            marker: false,
            circlemarker: false,
            rectangle: true
        },
        edit: {
            featureGroup: drawnItems
        }
    });
    map.addControl(drawControl);

    // Capture the bounding box
    map.on(L.Draw.Event.CREATED, function (e) {
        var type = e.layerType, layer = e.layer;
        console.log('type:', type);
        if (type === 'rectangle') {
            var bounds = layer.getBounds();
            var ne = bounds.getNorthEast();
            var sw = bounds.getSouthWest();

            // Store coordinates in the hidden form
            document.getElementById('ne_lat').value = ne.lat;
            document.getElementById('ne_lng').value = ne.lng;
            document.getElementById('sw_lat').value = sw.lat;
            document.getElementById('sw_lng').value = sw.lng;

            drawnItems.addLayer(layer);
        }
    });
});
