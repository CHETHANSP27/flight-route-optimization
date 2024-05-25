import requests
import heapq
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# Configuration - replace these with your actual API key
OPENWEATHERMAP_API_KEY = 'd67a14e9bf6faf56d86d335b0eb6ae57'

# Static data for aircraft performance (as an example)
AIRCRAFT_PERFORMANCE_DATA = {
    "Boeing737": {
        "fuel_burn_rate": 0.5  # Gallons per mile
    }
}

# Static airport coordinates for illustration purposes
AIRPORT_COORDINATES = {
    "JFK": {"lat": 40.6413, "lon": -73.7781},
    "LAX": {"lat": 33.9416, "lon": -118.4085}
}

# Function to get weather data from OpenWeatherMap
def get_weather_data(latitude, longitude):
    url = f"http://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid={OPENWEATHERMAP_API_KEY}"
    response = requests.get(url)
    return response.json()

# Function to get vehicle performance data (from static data in this example)
def get_vehicle_performance_data(aircraft_model):
    return AIRCRAFT_PERFORMANCE_DATA.get(aircraft_model, None)

# Function to calculate fuel cost
def calculate_fuel_cost(distance, fuel_burn_rate, fuel_price):
    return distance * fuel_burn_rate * fuel_price

# Heuristic function for A* (Haversine distance)
def haversine_distance(lat1, lon1, lat2, lon2):
    from math import radians, sin, cos, sqrt, atan2

    R = 3956  # Radius of the Earth in miles
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

# A* search algorithm
def a_star_search(origin, destination, aircraft_model, fuel_price):
    waypoints = [
        {"code": origin['code'], "lat": origin['lat'], "lon": origin['lon']},
        {"code": destination['code'], "lat": destination['lat'], "lon": destination['lon']}
    ]

    vehicle_data = get_vehicle_performance_data(aircraft_model)
    if not vehicle_data:
        return {"error": "Aircraft model not found in performance database."}

    fuel_burn_rate = vehicle_data['fuel_burn_rate']

    # Priority queue for A* (min-heap)
    open_set = []
    heapq.heappush(open_set, (0, origin['code'], 0, []))  # (estimated_total_cost, current_airport_code, current_cost, path)

    # Dictionary to store the cost to reach each waypoint
    g_costs = {origin['code']: 0}
    closed_set = set()

    while open_set:
        _, current_airport_code, current_cost, path = heapq.heappop(open_set)

        if current_airport_code == destination['code']:
            total_distance = sum(waypoint['distance_to_next'] for waypoint in path if 'distance_to_next' in waypoint)
            total_fuel_cost = calculate_fuel_cost(total_distance, fuel_burn_rate, fuel_price)
            return {
                "total_distance": total_distance,
                "total_fuel_cost": total_fuel_cost,
                "path": path
            }

        closed_set.add(current_airport_code)

        for waypoint in waypoints:
            next_airport_code = waypoint['code']
            if next_airport_code == current_airport_code:
                continue

            distance_to_next = haversine_distance(
                AIRPORT_COORDINATES[current_airport_code]['lat'],
                AIRPORT_COORDINATES[current_airport_code]['lon'],
                AIRPORT_COORDINATES[next_airport_code]['lat'],
                AIRPORT_COORDINATES[next_airport_code]['lon']
            )

            latitude, longitude = AIRPORT_COORDINATES[next_airport_code]['lat'], AIRPORT_COORDINATES[next_airport_code]['lon']

            if next_airport_code in closed_set:
                continue

            # Weather check
            weather_data = get_weather_data(latitude, longitude)
            if weather_data['weather'][0]['main'] in ['Thunderstorm', 'Extreme']:
                continue

            new_cost = current_cost + distance_to_next
            if new_cost < g_costs.get(next_airport_code, float('inf')):
                g_costs[next_airport_code] = new_cost
                heuristic = haversine_distance(latitude, longitude, destination['lat'], destination['lon'])
                estimated_total_cost = new_cost + heuristic
                new_path = path + [{"code": next_airport_code, "distance_to_next": distance_to_next}]
                heapq.heappush(open_set, (estimated_total_cost, next_airport_code, new_cost, new_path))

    return {"error": "No feasible route found."}


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/optimize-route', methods=['POST'])
@app.route('/optimize-route', methods=['POST'])
def optimize_route():
    data = request.json
    origin_code = data.get('departure')
    destination_code = data.get('arrival')
    aircraft_model = data.get('aircraft_model')
    fuel_price = data.get('fuel_price')

    origin = AIRPORT_COORDINATES.get(origin_code)
    destination = AIRPORT_COORDINATES.get(destination_code)

    if not origin or not destination:
        return jsonify({"error": "Invalid airport code(s). Please try again."}), 400

    origin['code'] = origin_code
    destination['code'] = destination_code

    result = a_star_search(origin, destination, aircraft_model, fuel_price)

    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True)