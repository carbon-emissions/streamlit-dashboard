import json
import requests

# Function to calculate emissions per passenger
def calculate_emissions(vehicle_type, fuel_type, total_km, num_passengers=1):
    with open('data/emissions_data.json', 'r') as f:
        data = json.load(f)
    
    for record in data:
        if record['Vehicle Type'] == vehicle_type and record['Fuel Type'] == fuel_type:
            emissions_per_km = record['Emissions/km(g)']
            break
    else:
        raise ValueError(f"No data found for {vehicle_type} with fuel type {fuel_type}")

    total_emissions = emissions_per_km * total_km
    emissions_per_passenger = total_emissions / num_passengers

    return emissions_per_passenger



GOOGLE_MAPS_API_KEY = "AIzaSyA8pRHkAHz2Zj45d2bTFwIt3V0F1PR9kA8"
base_url = "https://maps.googleapis.com/maps/api/directions/json"



import requests

# Function to calculate total distance (in km)
def get_total_distance_for_emissions(lat1, lon1, lat2, lon2, mode='driving'):
    base_url = "https://maps.googleapis.com/maps/api/directions/json"
    url = f"{base_url}?origin={lat1},{lon1}&destination={lat2},{lon2}&mode={mode}&key={GOOGLE_MAPS_API_KEY}"
    
    response = requests.get(url)

    if response.status_code == 200:
        directions = response.json()
        total_distance = 0

        if "routes" in directions and len(directions["routes"]) > 0:
            route = directions["routes"][0]
            for leg in route["legs"]:
                # Check mode: If it's transit, filter out non-transit steps
                for step in leg["steps"]:
                    if mode == 'transit':
                        if step['travel_mode'] == 'TRANSIT':  # Only count transit steps
                            total_distance += step['distance']['value']
                    else:
                        total_distance += step['distance']['value']  # Count all steps for driving
                
            return total_distance / 1000  # Convert meters to km
        
        else:
            return "Could Not Calculate Total Distance"
    
    else:
        return f"Error fetching route data: {response.status_code}"
