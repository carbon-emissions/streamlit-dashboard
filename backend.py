import json
import requests
import googlemaps

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
gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)

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
    


# Function to get coordinates from an address
def get_coordinates(address):
    try:
        result = gmaps.geocode(address)
        if result:
            location = result[0]["geometry"]["location"]
            return (location["lat"], location["lng"])
        return None
    except Exception:
        return None    



def get_route_data(origin, destination, mode="driving"):
    """Fetch route details from Google Maps API based on selected mode."""
    origin_coords = get_coordinates(origin)
    destination_coords = get_coordinates(destination)

    if not origin_coords or not destination_coords:
        return "Error fetching coordinates."

    base_url = "https://maps.googleapis.com/maps/api/directions/json"

    # Build API request URL dynamically
    url = f"{base_url}?origin={origin_coords[0]},{origin_coords[1]}&destination={destination_coords[0]},{destination_coords[1]}&mode={mode}&key={GOOGLE_MAPS_API_KEY}"
    response = requests.get(url)

    if response.status_code == 200:
        directions = response.json()
        travel_data = []
        encoded_polyline = ""

        if "routes" in directions and len(directions["routes"]) > 0:
            route = directions["routes"][0]
            encoded_polyline = route["overview_polyline"]["points"]

            for leg in route["legs"]:
                for step_index, step in enumerate(leg["steps"]):
                    step_info = {
                        "mode": step["travel_mode"].lower(),
                        "instruction": step["html_instructions"],
                        "distance": step["distance"]["text"],
                        "duration": step["duration"]["text"],
                    }

                    # Handle transit mode details
                    if step_info["mode"] == "transit" and "transit_details" in step:
                        transit = step["transit_details"]
                        step_info.update({
                            "transit_line": transit.get("line", {}).get("name", "Unknown Line"),
                            "vehicle": transit.get("line", {}).get("vehicle", {}).get("name", "Unknown Vehicle"),
                            "departure_stop": transit.get("departure_stop", {}).get("name", "Unknown Stop"),
                            "arrival_stop": transit.get("arrival_stop", {}).get("name", "Unknown Stop"),
                        })

                        # Walking before/after transit
                        if step_index > 0 and leg["steps"][step_index - 1]["travel_mode"].lower() == "walking":
                            step_info["walking_before"] = f"{leg['steps'][step_index - 1]['distance']['text']} (Duration: {leg['steps'][step_index - 1]['duration']['text']})"

                        if step_index < len(leg["steps"]) - 1 and leg["steps"][step_index + 1]["travel_mode"].lower() == "walking":
                            step_info["walking_after"] = f"{leg['steps'][step_index + 1]['distance']['text']} (Duration: {leg['steps'][step_index + 1]['duration']['text']})"

                    travel_data.append(step_info)

        return travel_data, encoded_polyline
    else:
        return f"Error fetching route data: {response.status_code}"