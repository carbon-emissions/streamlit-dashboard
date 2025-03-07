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

import streamlit as st
import googlemaps
import math
from streamlit_folium import st_folium
import folium
import pathlib
import re
from geminiAPI import *


# Streamlit UI
st.set_page_config(page_title="CO₂de Red", layout="wide")
# st.title(":car: CO₂de Red")

# centred but image not visible
# st.markdown("""
#     <div style="text-align: center;">
#         <img src="content/logo.png" width="150">
#     </div>
# """, unsafe_allow_html=True)

# col1, col2 = st.columns([0.05, 0.95])  # First column 5%, second 95%
# with col1:
#     st.image("content/logo.png", use_container_width=False, width=75)
# with col2:
#     st.markdown("""
#         <h1 style="text-align: left; margin-left: -20px; font-size: 48px; color: #8A0000;">CO₂de Red</h1>""", unsafe_allow_html=True)



st.image("content/logo.png", use_container_width=False, width=75)

st.markdown("<h1 style='text-align: center;'>CO₂de Red</h1>", unsafe_allow_html=True)

st.write("Enter or click on the map to set your start and end locations.")

# Custom CSS for the top navbar
st.markdown("""
    <style>
        .top-bar {
            background-color: #D32F2F; /* Red color */
            height: 10px; /* Adjust height as needed */
            width: 100%;
            position: fixed;
            top: 0;
            left: 0;
            z-index: 9999;
        }
    </style>
    <div class="top-bar"></div>
""", unsafe_allow_html=True)

st.markdown("""
<style>
.large-font {
    font-size: 30px !important;
}
</style>
""", unsafe_allow_html=True)

with open('data/emissions_data.json', 'r') as f:
    data = json.load(f)

# Extract unique vehicle types and fuel types
vehicle_types = { 
    'Transit' if entry['Vehicle Type'] in ['Bus', 'Subway'] else entry['Vehicle Type'] 
    for entry in data
}

# Define the preferred order for vehicle types
VEHICLE_ORDER = ["Transit", "Passenger", "Minivan", "SUV"]

# Sort vehicle types based on the predefined order
VEHICLE_TYPES = sorted(vehicle_types, key=lambda x: VEHICLE_ORDER.index(x) if x in VEHICLE_ORDER else len(VEHICLE_ORDER))

fuel_types = {entry['Fuel Type'] for entry in data if entry['Fuel Type'] is not None}

FUEL_ORDER = ["Gasoline", "Diesel", "Natural Gas", "Zero Emission Vehicles", "Other"]
FUEL_TYPES = sorted(fuel_types, key=lambda x: FUEL_ORDER.index(x) if x in FUEL_ORDER else len(FUEL_ORDER))


def decode_polyline(encoded_polyline):
    return polyline.decode(encoded_polyline)



# Function to get place name from coordinates (Reverse Geocoding)
def get_place_name(lat, lon):
    try:
        result = gmaps.reverse_geocode((lat, lon))
        if result:
            return result[0]["formatted_address"]
        return "Unknown Location"
    except Exception:
        return "Unknown Location"
   


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



def calculate_emissions_transit(transit_type, distance, data):
    emissions_per_km = next((item["Emissions/km(g)"] for item in data if item["Vehicle Type"] == transit_type), 0)
    return distance * emissions_per_km



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
    
# function to reset map
def reset_map():
    st.session_state.map_center = {"lat": INITIAL_LAT, "lon": INITIAL_LONG, "zoom": INITIAL_ZOOM}
    st.session_state.start_coords = None  # Reset start marker
    st.session_state.end_coords = None  # Reset end marker
    st.session_state.encoded_polyline = None  # Remove the polyline
    st.session_state.route_data = None  # Remove route data
    st.session_state.emissions = None  # Reset emissions
    st.session_state.distance = None  # Reset distance
    st.session_state.refresh_map = True  # Force refresh
    st.rerun()

# function to reset only the zoom level
def reset_zoom():
    st.session_state.map_center = {"lat": INITIAL_LAT, "lon": INITIAL_LONG, "zoom": INITIAL_ZOOM}
    st.session_state.refresh_map = True  # Force refresh
    st.rerun()

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

# If route data exists, add the polyline
if "encoded_polyline" in st.session_state and st.session_state["encoded_polyline"]:
    decoded_polyline = decode_polyline(st.session_state["encoded_polyline"])
    folium.PolyLine(decoded_polyline, color="blue", weight=5, opacity=0.8).add_to(m)

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

# Add a button to reset map
st.button("Clear Current Selected Locations", on_click=reset_map)

# Select vehicle type
vehicle_type = st.selectbox(":train2: Select Vehicle Type", VEHICLE_TYPES)

# Check if vehicle type changed and clear previous data
if "last_vehicle_type" not in st.session_state:
    st.session_state["last_vehicle_type"] = vehicle_type

if vehicle_type != st.session_state["last_vehicle_type"]:
    st.session_state["last_vehicle_type"] = vehicle_type  # Update last selected type
    st.session_state.pop("emissions", None)
    st.session_state.pop("distance", None)
    st.session_state.pop("route_data", None)
    st.session_state.pop("encoded_polyline", None)
    st.rerun()  # Force a rerun to clear old data

# Only show fuel type if NOT using public transport

if vehicle_type in ["Passenger", "Minivan", "SUV"]:
    fuel_type = st.radio(":fuelpump: Select Fuel Type", FUEL_TYPES, horizontal=True)
    num_passengers = st.number_input("Number of Passengers", min_value=1, max_value=6, value=1)
else:
    fuel_type = None  # Fuel type is not needed for public transport

# Add a button to reset the zoom level
st.button("Reset Zoom", on_click=reset_zoom)

# Button to calculate emissions
if st.button("Calculate Emissions"):
    if st.session_state["start_coords"] and st.session_state["end_coords"]:
        start_coords = st.session_state["start_coords"]
        end_coords = st.session_state["end_coords"]
        start_address = st.session_state["start_name"]
        end_address = st.session_state["end_name"]

        # Set the mode dynamically based on vehicle type
        mode = 'driving' if vehicle_type in ['Passenger', 'Minivan', 'SUV'] else 'transit'

        route_data, encoded_polyline = get_route_data(start_address, end_address, mode=mode)

        try:
            if fuel_type is not None:
                total_distance = get_total_distance_for_emissions(start_coords[0], start_coords[1], end_coords[0], end_coords[1], mode=mode)
                emissions_per_passenger = calculate_emissions(vehicle_type, fuel_type, total_distance, num_passengers)
                emissions_in_kg = emissions_per_passenger / 1000  # Convert g to kg CO₂
            else:
                transit_distances = calculate_transit_distances(route_data)
                total_distance = sum(transit_distances.values())
                total_emissions = sum(distance * next((item["Emissions/km(g)"] for item in data if item["Vehicle Type"] == transit_type), 0) for transit_type, distance in transit_distances.items())
                emissions_in_kg = total_emissions / 1000  # Convert grams to kilogram
                st.session_state['transit_distances'] = transit_distances
            
            # Store results and route data in session state
            st.session_state['emissions'] = emissions_in_kg
            st.session_state['distance'] = total_distance
            st.session_state['route_data'] = route_data
            st.session_state['encoded_polyline'] = encoded_polyline
        
        except ValueError as e:
            st.error(f"Error: {e}")

        st.rerun()  # Force rerun to update the map
    else:
        st.error("Please select both a start and end location on the map.")
        
if 'emissions' in st.session_state and st.session_state['emissions'] is not None:
    # Create two columns for side-by-side layout
    col1, col2 = st.columns(2)

    with col1:
        # Green card for emissions with red first line and black second line
        st.markdown(f"""
        <div style="background-color: #AFE1AF; padding: 30px; text-align: center; border-radius: 10px; font-size: 28px;">
            <span style="color: #FF3131;">{st.session_state['emissions']:.2f} kg CO2e</span>
            <div style="color: black; font-size: 16px; margin-top: 10px;">Average Emissions for your trip</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        # Green card for distance with red first line and black second line
        st.markdown(f"""
        <div style="background-color: #AFE1AF; padding: 30px; text-align: center; border-radius: 10px; font-size: 28px;">
            <span style="color: #FF3131;">{st.session_state['distance']:.2f} km</span>
            <div style="color: black; font-size: 16px; margin-top: 10px;">Travel distance in the selected mode of transport</div>
        </div>
        """, unsafe_allow_html=True)


def extract_numeric_time(value):
    match = re.search(r"[\d\.]+", value)  # Extracts number (supports decimals)
    return float(match.group()) if match else 0  # Converts to float if found, otherwise returns 0
        

# Display route data in horizontal boxes
if 'route_data' in st.session_state and st.session_state['route_data'] is not None:
    st.write("## Route Details")

    if vehicle_type == "Transit":
        for step in st.session_state['route_data']:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if step['mode'] == 'walking':
                    st.markdown("### :walking: Transportation Mode")
                    st.write(step['mode'].capitalize())
                elif step['mode'] == 'transit':
                    if step['vehicle'] == 'Bus':
                        st.markdown("### :bus: Transportation Mode")
                        st.write(step['vehicle'].capitalize() + " (" + step['transit_line'] + ")")
                    elif step['vehicle'] == 'Subway':
                        st.markdown("### :bullettrain_side: Transportation Mode")
                        st.write(step['vehicle'].capitalize() + " (" + step['transit_line'] + ")")

            with col2:
                st.markdown("### :straight_ruler: Distance Travelled")
                st.write(f"{step['distance']}")  # Assuming distance is in km

            with col3:
                st.markdown("### ⏳ Approximate Duration")
                st.write(step['duration'])

            with col4:
                st.markdown("### 🌿 Emissions")
                if step['mode'] == 'transit':
                    emissions = calculate_emissions_transit(step['vehicle'], float(re.search(r'\d+\.\d+', step['distance']).group()), data)
                    st.write(f"{emissions:.0f} g")
                else:
                    st.write("0 g")  # Assuming walking has zero emissions

            st.divider()


    else:
        # Extract numeric values for summation
        if 'distance' in st.session_state:
            total_distance = st.session_state['distance']
        total_duration = sum(extract_numeric_time(step['duration']) for step in st.session_state['route_data'])
        mode = st.session_state['route_data'][0]['mode']  # Use mode from first step
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### :car: Transportation Mode")
            st.write(mode.capitalize())  # Display transport mode

        with col2:
            st.markdown("### :straight_ruler: Distance Travelled")
            st.write(f"{total_distance} km")  # Display total distance

        with col3:
            st.markdown("### ⏳ Approximate Duration")
            st.write(f"{total_duration} min")  # Display total duration
        
        st.divider()
        

     

    feedback = get_ai_feedback(st.session_state['route_data'])
    st.markdown(f'<p class="large-font">{feedback}</p>', unsafe_allow_html=True)
