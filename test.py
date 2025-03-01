import streamlit as st
import requests
from dotenv import load_dotenv
import os

API_KEY = os.getenv("GOOGLE_API_KEY")

def get_place_suggestions(query):
    """Fetch place suggestions from Google Places API Autocomplete"""
    url = f"https://maps.googleapis.com/maps/api/place/autocomplete/json"
    params = {
        "input": query,
        "key": API_KEY,
        "types": "geocode",  # Restrict results to addresses
        "components": "country:ca"
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        predictions = response.json().get("predictions", [])
        return [place["description"] for place in predictions]
    return []

def get_place_coordinates(place_id):
    """Fetch place details (latitude, longitude) using Place ID"""
    url = f"https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "key": API_KEY,
        "fields": "geometry/location"  # Get latitude and longitude
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        location = response.json().get("result", {}).get("geometry", {}).get("location", {})
        return location.get("lat"), location.get("lng")
    return None, None

# Streamlit UI
st.title("Google Maps Places Autocomplete in Streamlit")

# User input
query = st.text_input("Enter origin or destination:")

# Fetch autocomplete suggestions
if query:
    suggestions = get_place_suggestions(query)
    if suggestions:
        selected_place = st.selectbox("Select a place:", suggestions)
        
        if selected_place:
            # Extract place_id from API response
            url = f"https://maps.googleapis.com/maps/api/place/autocomplete/json"
            params = {"input": selected_place, "key": API_KEY}
            response = requests.get(url, params=params)
            if response.status_code == 200:
                place_id = response.json()["predictions"][0]["place_id"]
                lat, lng = get_place_coordinates(place_id)
                st.write(f"**Selected Location:** {selected_place}")
                st.write(f"**Latitude:** {lat}, **Longitude:** {lng}")
    else:
        st.write("No suggestions available.")

# # Load environment variables
# API_KEY = os.getenv("GOOGLE_API_KEY")

# def get_place_suggestions(query):
#     """Fetch place suggestions from Google Places API Autocomplete"""
#     url = "https://maps.googleapis.com/maps/api/place/autocomplete/json"
#     params = {
#         "input": query,
#         "key": API_KEY,
#         "types": "geocode",  # Restrict results to addresses
#         "components": "country:ca"
#     }
#     response = requests.get(url, params=params)
    
#     if response.status_code == 200:
#         data = response.json()
#         predictions = data.get("predictions", [])
#         return [(place["description"], place["place_id"]) for place in predictions]
    
#     return []

# def get_place_coordinates(place_id):
#     """Fetch place details (latitude, longitude) using Place ID"""
#     url = "https://maps.googleapis.com/maps/api/place/details/json"
#     params = {
#         "place_id": place_id,
#         "key": API_KEY,
#         "fields": "geometry/location"  # Get latitude and longitude
#     }
#     response = requests.get(url, params=params)
    
#     if response.status_code == 200:
#         data = response.json()
#         location = data.get("result", {}).get("geometry", {}).get("location", {})
#         return location.get("lat"), location.get("lng")
    
#     return None, None

# # Streamlit UI
# st.title("Google Maps Places Autocomplete in Streamlit")

# # User input
# query = st.text_input("Enter origin or destination:")

# # Fetch autocomplete suggestions
# if query:
#     suggestions = get_place_suggestions(query)
    
#     if suggestions:
#         place_names = [place[0] for place in suggestions]  # Extract place descriptions
#         selected_place = st.selectbox("Select a place:", place_names)

#         if selected_place:
#             # Find the corresponding place_id
#             place_id = dict(suggestions)[selected_place]
#             lat, lng = get_place_coordinates(place_id)

#             # Display the results
#             st.write(f"**Selected Location:** {selected_place}")
#             if lat and lng:
#                 st.write(f"**Latitude:** {lat}, **Longitude:** {lng}")
#             else:
#                 st.error("Could not fetch coordinates. Please try another place.")
#     else:
#         st.warning("No suggestions available. Try a different search query.")
