import streamlit as st
import folium
from streamlit_folium import folium_static
import requests
from geopy.geocoders import Nominatim
import math
import googlemaps
import openai  # Assuming AI feedback is handled by OpenAI API

# Set API keys
GOOGLE_MAPS_API_KEY = "AIzaSyA8pRHkAHz2Zj45d2bTFwIt3V0F1PR9kA8"
OPENAI_API_KEY = "YOUR_OPENAI_API_KEY"

# Initialize Google Maps API client
gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)

# Transport types & emission factors (g/km)
TRANSPORT_TYPES = {
    "Gas Car": 170,
    "Electric Car": 128,
    "Bus": 31,
}

# Function to get coordinates from an address
def get_coordinates(address):
    try:
        geolocator = Nominatim(user_agent="geoapi")
        location = geolocator.geocode(address)
        return (location.latitude, location.longitude) if location else None
    except Exception as e:
        return None

# Function to calculate Haversine distance (in km)
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Radius of Earth in km
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = math.sin(d_lat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# Function to get route data from Google Maps Directions API
def get_route_data(start_coords, end_coords, mode="driving"):
    try:
        directions = gmaps.directions(
            origin=start_coords, destination=end_coords, mode=mode
        )
        if not directions:
            return None, "No route found"
        distance_km = directions[0]["legs"][0]["distance"]["value"] / 1000
        return distance_km, None
    except Exception as e:
        return None, str(e)

# Function to get AI feedback using OpenAI
def get_ai_feedback(distance, emissions, transport_type):
    prompt = f"""
    Provide a brief assessment of a journey:
    - Distance: {distance} km
    - Transport Type: {transport_type}
    - CO2 Emissions: {emissions:.2f} kg CO2
    Suggest alternative eco-friendly transport options if applicable.
    """
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    return response["choices"][0]["message"]["content"]

# Streamlit UI
st.set_page_config(page_title="Emission Calculator", layout="wide")

st.title(":car: Footprint Emission Calculator")
st.write("Enter a start and end location to calculate emissions.")

col1, col2 = st.columns(2)

with col1:
    start_address = st.text_input(":round_pushpin: Start Location", "Vancouver, BC")
with col2:
    end_address = st.text_input(":round_pushpin: End Location", "Toronto, ON")

transport_type = st.selectbox(":train2: Select Transport Type", list(TRANSPORT_TYPES.keys()))

if st.button("Calculate Emissions"):
    start_coords = get_coordinates(start_address)
    end_coords = get_coordinates(end_address)

    if start_coords and end_coords:
        distance, error = get_route_data(start_coords, end_coords, mode="driving")

        if error:
            st.error(error)
        else:
            emission_factor = TRANSPORT_TYPES[transport_type]
            emissions = (distance * emission_factor) / 1000  # Convert g to kg CO2

            # AI-generated feedback
            ai_feedback = get_ai_feedback(distance, emissions, transport_type)

            st.success(f":straight_ruler: Distance: {distance:.2f} km")
            st.success(f":dash: CO₂ Emissions: {emissions:.2f} kg")
            st.info(f":robot_face: AI Feedback: {ai_feedback}")

            # Map Visualization
            m = folium.Map(location=start_coords, zoom_start=5)
            folium.Marker(start_coords, popup="Start", icon=folium.Icon(color="green")).add_to(m)
            folium.Marker(end_coords, popup="End", icon=folium.Icon(color="red")).add_to(m)
            folium.PolyLine([start_coords, end_coords], color="blue").add_to(m)
            folium_static(m)
    else:
        st.error("Could not find coordinates for one or both locations. Please enter valid addresses.")