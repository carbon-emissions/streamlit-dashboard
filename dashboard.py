import streamlit as st
import folium
from streamlit_folium import folium_static, st_folium
import googlemaps
from folium.plugins import Geocoder
from folium.plugins import LocateControl
from geopy.geocoders import Nominatim
from backend import *
import json
import requests
import polyline

# Set API keys (Replace with your actual keys)
GOOGLE_MAPS_API_KEY = "AIzaSyA8pRHkAHz2Zj45d2bTFwIt3V0F1PR9kA8"

# Initialize Google Maps API client
gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)

with open('data/emissions_data.json', 'r') as f:
    data = json.load(f)

# Extract unique vehicle types and fuel types
vehicle_types = { 
    'Transit' if entry['Vehicle Type'] in ['Bus', 'Subway'] else entry['Vehicle Type'] 
    for entry in data
}
fuel_types = {entry['Fuel Type'] for entry in data}

VEHICLE_TYPES = list(vehicle_types)
FUEL_TYPES = list(fuel_types)



def decode_polyline(encoded_polyline):
    return polyline.decode(encoded_polyline)



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



# Function to get place name from coordinates (Reverse Geocoding)
def get_place_name(lat, lon):
    try:
        result = gmaps.reverse_geocode((lat, lon))
        if result:
            return result[0]["formatted_address"]
        return "Unknown Location"
    except Exception:
        return "Unknown Location"


    
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
    


def calculate_transit_distances(route_data):
    transit_distances = {}
    for segment in route_data:
        if segment['mode'] == 'transit' and 'vehicle' in segment:
            vehicle = segment['vehicle']
            distance = float(segment['distance'].split()[0])
            if vehicle in transit_distances:
                transit_distances[vehicle] += distance
            else:
                transit_distances[vehicle] = distance
    return transit_distances

# Streamlit UI
st.set_page_config(page_title="Emission Calculator", layout="wide")
st.title(":car: CO₂de Red")
st.write("Enter or click on the map to set your start and end locations.")

# Default map center at Vancouver
INITIAL_LAT = 49.2827
INITIAL_LONG = -123.1207
vancouver_center = (INITIAL_LAT, INITIAL_LONG)
INITIAL_ZOOM = 12

# Default zoom level
# if 'zoom_level' not in st.session_state:

# initialize session state and start and end coords
if "map_center" not in st.session_state:
    st.session_state.map_center = {"lat": INITIAL_LAT, "lon": INITIAL_LONG, "zoom": INITIAL_LONG}

if "start_coords" not in st.session_state:
    st.session_state["start_coords"] = None
    st.session_state["start_name"] = None

if "end_coords" not in st.session_state:
    st.session_state["end_coords"] = None
    st.session_state["end_name"] = None
    
# function to reset zoom and center
def reset_map():
    st.session_state.map_center = {"lat": INITIAL_LAT, "lon": INITIAL_LONG, "zoom": INITIAL_LONG}

# UI for manual input of locations
col1, col2 = st.columns(2)
with col1:
    start_address = st.text_input("Start Location (Enter Street Address or Click Map)")
    if st.button("Set Start"):
        coords = get_coordinates(start_address)
        if coords:
            st.session_state["start_coords"] = coords
            st.session_state["start_name"] = start_address
        else:
            st.error("Could not find location. Try again.")

with col2:
    end_address = st.text_input("End Location (Enter Street Address or Click Map)")
    if st.button("Set End"):
        coords = get_coordinates(end_address)
        if coords:
            st.session_state["end_coords"] = coords
            st.session_state["end_name"] = end_address
        else:
            st.error("Could not find location. Try again.")

# Define the map
# m = folium.Map(location=vancouver_center, zoom_start=12)
# folium.plugins.Geocoder().add_to(m)

# Create map and add markers if locations are selected
m = folium.Map(location=vancouver_center, zoom_start=INITIAL_ZOOM)

if st.session_state["start_coords"]:
    folium.Marker(
        st.session_state["start_coords"],
        popup=f"Start: {st.session_state['start_name']}",
        icon=folium.Icon(color="green"),
    ).add_to(m)

if st.session_state["end_coords"]:
    folium.Marker(
        st.session_state["end_coords"],
        popup=f"End: {st.session_state['end_name']}",
        icon=folium.Icon(color="red"),
    ).add_to(m)

# Clickable Map
map_data = st_folium(m, height=500, width=1400)

# If a new point is clicked, update start or end point
if map_data and map_data.get("last_clicked"):
    lat, lon = map_data["last_clicked"]["lat"], map_data["last_clicked"]["lng"]
    place_name = get_place_name(lat, lon)

    if not st.session_state["start_coords"]:
        st.session_state["start_coords"] = (lat, lon)
        st.session_state["start_name"] = place_name
    else:
        st.session_state["end_coords"] = (lat, lon)
        st.session_state["end_name"] = place_name

# Display selected locations
col1, col2 = st.columns(2)
with col1:
    if st.session_state["start_coords"]:
        st.success(f"Start: {st.session_state['start_name']} ({st.session_state['start_coords']})")

with col2:
    if st.session_state["end_coords"]:
        st.success(f"End: {st.session_state['end_name']} ({st.session_state['end_coords']})")

# Select vehicle type
vehicle_type = st.selectbox(":train2: Select Vehicle Type", VEHICLE_TYPES)

# Only show fuel type if NOT using public transport
if vehicle_type in ["Passenger", "Minivan", "SUV"]:
    fuel_type = st.radio(":fuelpump: Select Fuel Type", FUEL_TYPES, horizontal=True)
else:
    fuel_type = None  # Fuel type is not needed for public transport

# Select number of passengers in vehicle
num_passengers = st.number_input("Number of Passengers", min_value=1, max_value=6, value=1)

# Add a button to reset the zoom level
st.button("Reset Zoom", on_click=reset_map)


# Button to calculate emissions
if st.button("Calculate Emissions"):
    if st.session_state["start_coords"] and st.session_state["end_coords"]:
        start_coords = st.session_state["start_coords"]
        end_coords = st.session_state["end_coords"]
        start_address = st.session_state["start_name"]
        end_address = st.session_state["end_name"]

       # Set the mode dynamically based on vehicle type
        mode = 'driving' if vehicle_type in ['Passenger', 'Minivan', 'SUV'] else 'transit'

        # Calculate the total distance
        distance = get_total_distance_for_emissions(start_coords[0], start_coords[1], end_coords[0], end_coords[1], mode=mode)
        route_data, encoded_polyline = get_route_data(start_address, end_address, mode=mode)


        # Calculate emissions using the new function
        try:
            if fuel_type is not None:
                # Calculate emissions for fuel-based vehicle types (e.g., cars)
                emissions_per_passenger = calculate_emissions(vehicle_type, fuel_type, distance, num_passengers)
                emissions_in_kg = emissions_per_passenger / 1000  # Convert g to kg CO₂
            else:
                # If fuel_type is None, it implies we're using public transit, so calculate emissions based on transit distances
                transit_distances = calculate_transit_distances(route_data)
                
                # Now calculate the emissions for each transit type (Bus, Subway, etc.)
                total_emissions = 0
                for transit_type, distance in transit_distances.items():
                    # Find the emissions per km for the transit type
                    vehicle_info = next((item for item in data if item["Vehicle Type"] == transit_type), None)
                    
                    if vehicle_info:
                        emissions_per_km = vehicle_info["Emissions/km(g)"]
                        emissions = distance * emissions_per_km  # emissions in grams
                        total_emissions += emissions
                
                # Convert total emissions to kg
                emissions_in_kg = total_emissions / 1000  # Convert grams to kilograms
            
            # Store results in session state
            st.session_state['emissions'] = emissions_in_kg
            st.session_state['distance'] = distance

            # Store route data in session state
            st.session_state['route_data'] = route_data
            st.session_state['encoded_polyline'] = encoded_polyline

            # Display results
            # st.success(f":straight_ruler: Distance: {distance:.2f} km")
            # st.success(f":dash: CO₂ Emissions per Passenger: {emissions_in_kg:.2f} kg")
        except ValueError as e:
            st.error(f"Error: {e}")

        # Update map with route
        m = folium.Map(location=start_coords, zoom_start=INITIAL_ZOOM)
        folium.Marker(start_coords, popup=f"Start: {st.session_state['start_name']}", icon=folium.Icon(color="green")).add_to(m)
        folium.Marker(end_coords, popup=f"End: {st.session_state['end_name']}", icon=folium.Icon(color="red")).add_to(m)

        # Decode and add the polyline to the map
        if encoded_polyline:
            decoded_polyline = decode_polyline(encoded_polyline)
            decoded_polyline = [list(tup) for tup in decoded_polyline]
            folium.PolyLine(decoded_polyline, color="blue", weight=5, opacity=0.8).add_to(m)

        st_folium(m, height=700, width=1200)
    else:
        st.error("Please select both a start and end location on the map.")

if 'emissions' in st.session_state:
    st.write(f"Average Emissions for your trip: {st.session_state['emissions']:.2f}")
    st.write(f"Distance travelled in the selected mode of transport: {st.session_state['distance']:.2f} km")        

# Display route data
if 'route_data' in st.session_state:
    st.write("## Route Details")
    for step in st.session_state['route_data']:
        st.write(f"**Mode:** {step['mode']}")
        # st.write(f"**From:** {step['departure_stop']}")
        # st.write(f"**To:** {step['arrival_stop']}")
        st.write(f"**Distance:** {step['distance']}")
        if 'walking_before' in step:
            st.write(f"**Walking before:** {step['walking_before']}")
        if 'walking_after' in step:
            st.write(f"**Walking after:** {step['walking_after']}")
        st.write("---")