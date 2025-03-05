import streamlit as st
import folium
from streamlit_folium import folium_static, st_folium
import googlemaps
import openai
import math
from folium.plugins import Geocoder
from folium.plugins import LocateControl
from geopy.geocoders import Nominatim
from backend import calculate_emissions
import json

# Set API keys (Replace with your actual keys)
GOOGLE_MAPS_API_KEY = "AIzaSyA8pRHkAHz2Zj45d2bTFwIt3V0F1PR9kA8"
OPENAI_API_KEY = "YOUR_OPENAI_API_KEY"

# Initialize Google Maps API client
gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)

with open('data/emissions_data.json', 'r') as f:
    data = json.load(f)

# Extract unique vehicle types and fuel types
vehicle_types = {entry['Vehicle Type'] for entry in data}
fuel_types = {entry['Fuel Type'] for entry in data}

VEHICLE_TYPES = list(vehicle_types)
FUEL_TYPES = list(fuel_types)


# # vehicle types  & emission factors (g/km) -> ADD VALUES FROM MODEL
# VEHICLE_TYPES = {
#     "Passenger": 170,
#     "Minivan": 128,
#     "SUV": 31,
#     "Bus": 234,
#     "Skytrain": 123,
#     "Seabus": 456
# }

# # fuel types  # DO WE NEED THIS TO BE DICTIONARY?!
# FUEL_TYPES = {
#     "Gasoline": 170,
#     "Diesel": 128,
#     "Natural Gas": 31,
#     "CH": 234,
#     "ZEV": 123,
#     "BEV": 456,
#     "PHEV": 93,
# }

# Function to calculate Haversine distance (in km)
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Radius of Earth in km
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = math.sin(d_lat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

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

# Function to get AI feedback
def get_ai_feedback(distance, emissions, vehicle_type):
    prompt = f"""
    Provide an assessment of this journey:
    - Distance: {distance:.2f} km
    - Transport Type: {vehicle_type}
    - CO₂ Emissions: {emissions:.2f} kg CO₂
    
    Suggest alternative eco-friendly transport options if applicable.
    """
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    return response["choices"][0]["message"]["content"]

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
if vehicle_type not in ["Skytrain", "Bus", "Seabus"]:
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

        # Calculate distance using Haversine formula
        distance = haversine(start_coords[0], start_coords[1], end_coords[0], end_coords[1])

        # Calculate emissions using the new function
        try:
            emissions_per_passenger = calculate_emissions(vehicle_type, fuel_type, distance, num_passengers)
            emissions_in_kg = emissions_per_passenger / 1000  # Convert g to kg CO₂

            # AI-generated feedback
            # ai_feedback = get_ai_feedback(distance, emissions, vehicle_type)

            # Store results in session state
            st.session_state['emissions'] = emissions_in_kg
            st.session_state['distance'] = distance

            # Display results
            # st.success(f":straight_ruler: Distance: {distance:.2f} km")
            # st.success(f":dash: CO₂ Emissions per Passenger: {emissions_in_kg:.2f} kg")
        except ValueError as e:
            st.error(f"Error: {e}")

        # Update map with route
        m = folium.Map(location=start_coords, zoom_start=INITIAL_ZOOM)
        folium.Marker(start_coords, popup=f"Start: {st.session_state['start_name']}", icon=folium.Icon(color="green")).add_to(m)
        folium.Marker(end_coords, popup=f"End: {st.session_state['end_name']}", icon=folium.Icon(color="red")).add_to(m)
        folium.PolyLine([start_coords, end_coords], color="blue").add_to(m)
        # Geocoder().add_to(m)
        st_folium(m, height=700, width=1200)
    else:
        st.error("Please select both a start and end location on the map.")

if 'emissions' in st.session_state:
    st.write(f"Emissions: {st.session_state['emissions']:.2f} kg per passenger")
    st.write(f"Distance: {st.session_state['distance']:.2f} km")        