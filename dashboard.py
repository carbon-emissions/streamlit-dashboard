import streamlit as st
import folium
from streamlit_folium import folium_static, st_folium
import googlemaps
import openai
import math
from folium.plugins import Geocoder
from folium.plugins import LocateControl
from geopy.geocoders import Nominatim

# Set API keys (Replace with your actual keys)
GOOGLE_MAPS_API_KEY = "AIzaSyA8pRHkAHz2Zj45d2bTFwIt3V0F1PR9kA8"
OPENAI_API_KEY = "YOUR_OPENAI_API_KEY"

# Initialize Google Maps API client
gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)

# vehicle types  & emission factors (g/km) -> ADD VALUES FROM MODEL
VEHICLE_TYPES = {
    "Passenger": 170,
    "Minivan": 128,
    "SUV": 31,
    "Bus": 234,
    "Skytrain": 123,
    "Seabus": 456
}

# fuel types  # DO WE NEED THIS TO BE DICTIONARY?!
FUEL_TYPES = {
    "Gasoline": 170,
    "Diesel": 128,
    "Natural Gas": 31,
    "CH": 234,
    "ZEV": 123,
    "BEV": 456,
    "PHEV": 93,
}

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
vancouver_center = (49.2827, -123.1207)
zoom_level = 12  

# Default zoom level
if 'zoom_level' not in st.session_state:
    st.session_state.zoom_level = 12  

# Initialize session state for start and end coordinates
if "start_coords" not in st.session_state:
    st.session_state["start_coords"] = None
    st.session_state["start_name"] = None

if "end_coords" not in st.session_state:
    st.session_state["end_coords"] = None
    st.session_state["end_name"] = None
    

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
m = folium.Map(location=vancouver_center, zoom_start=12)
# folium.plugins.Geocoder().add_to(m)
# Add markers if locations are selected
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
vehicle_type = st.selectbox(":train2: Select Vehicle Type", list(VEHICLE_TYPES.keys()))

# Select vehicle type
fuel_type = st.selectbox(":train2: Select Fuel Type", list(FUEL_TYPES.keys()))

# Add a button to reset the zoom level
if st.button('Reset Zoom'):
    st.session_state.zoom_level = 12  # Reset zoom level
    m.zoom_start = st.session_state.zoom_level

# Button to calculate emissions
if st.button("Calculate Emissions"):
    if st.session_state["start_coords"] and st.session_state["end_coords"]:
        start_coords = st.session_state["start_coords"]
        end_coords = st.session_state["end_coords"]

        # Calculate distance using Haversine formula
        distance = haversine(start_coords[0], start_coords[1], end_coords[0], end_coords[1])

        # Calculate emissions # need to fix -> how are we recording the different emission rates?
        emission_factor = VEHICLE_TYPES[vehicle_type]
        emissions = (distance * emission_factor) / 1000  # Convert g to kg CO2

        # AI-generated feedback
        ai_feedback = get_ai_feedback(distance, emissions, vehicle_type)

        # Display results
        st.success(f":straight_ruler: Distance: {distance:.2f} km")
        st.success(f":dash: CO₂ Emissions: {emissions:.2f} kg")
        st.info(f":robot_face: AI Feedback: {ai_feedback}")

        # Update map with route
        m = folium.Map(location=start_coords, zoom_start=12)
        folium.Marker(start_coords, popup=f"Start: {st.session_state['start_name']}", icon=folium.Icon(color="green")).add_to(m)
        folium.Marker(end_coords, popup=f"End: {st.session_state['end_name']}", icon=folium.Icon(color="red")).add_to(m)
        folium.PolyLine([start_coords, end_coords], color="blue").add_to(m)
        # Geocoder().add_to(m)
        st_folium(m, height=700, width=1200)
    else:
        st.error("Please select both a start and end location on the map.")