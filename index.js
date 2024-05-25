$(document).ready(function() {
    $("#search-btn").click(function() {
        var departure = $("#departure").val();
        var arrival = $("#arrival").val();
        var waypoints = $("#waypoints").val().split(',').map(w => w.trim());
        var aircraftModel = $("#aircraft_model").val();
        var fuelPrice = parseFloat($("#fuel_price").val());

        $.ajax({
            url: "/optimize-route",
            method: "POST",
            contentType: "application/json",
            data: JSON.stringify({
                departure: departure,
                arrival: arrival,
                waypoints: waypoints,
                aircraft_model: aircraftModel,
                fuel_price: fuelPrice
            }),
            success: function(data) {
                if (data.error) {
                    alert(data.error);
                } else {
                    alert(`Optimal Route Found: Total Distance = ${data.total_distance} miles, Total Fuel Cost = $${data.total_fuel_cost}`);

                    var map = L.map('map').setView([40.6413, -73.7781], 4);
                    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    }).addTo(map);

                    var path = data.path.map(waypoint => AIRPORT_COORDINATES[waypoint.code]);
                    var latlngs = path.map(coord => [coord.lat, coord.lon]);
                    L.polyline(latlngs, {color: 'blue'}).addTo(map);
                }
            }
        });
    });
});
