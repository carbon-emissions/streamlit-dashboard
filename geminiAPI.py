import requests
import json
import google.generativeai as genai
from backend import *

# API KEYS
GOOGLE_MAPS_API_KEY = "AIzaSyA8pRHkAHz2Zj45d2bTFwIt3V0F1PR9kA8"
GEMINI_API_KEY = "AIzaSyAlVaddDZPEljFsSzydrz7uKrGqo69Q1uU"

# Initialize Gemini AI
genai.configure(api_key=GEMINI_API_KEY)

def get_ai_feedback(travel_data):
    """Generates AI-based feedback using Gemini."""
    
    prompt = "Based on the route data from the google maps API below, based on the mode of transport and other factors you can consider, provide 3 key recommendations for the user to reduce their carbon emissions in this trip. Do not give an overall assesment, do not give emission estimates. Give exact usable recommendations (3) in a bullet point format and keep them concise.Do not include infrastructure recommendations for improvement but include how can the user emit less emission by providing alternative routes or modes of transportation.:\n\n"

    for step in travel_data:
        mode = step.get("mode", "Unknown Mode")
        distance = step.get("transit_distance", "N/A")
        walking_before = step.get("walking_before", "N/A")
        walking_after = step.get("walking_after", "N/A")

        prompt += f"🚍 Transit Mode: {mode}\n"
        prompt += f"📏 Transit Distance: {distance}\n"
        # prompt += f"🛑 Departure: {step['departure_stop']} ➡️ Arrival: {step['arrival_stop']}\n"

        if walking_before != "N/A":
            prompt += f"🚶 Walking Before Transit: {walking_before}\n"

        if walking_after != "N/A":
            prompt += f"🚶 Walking After Transit: {walking_after}\n"
        
        prompt += "\n"

    # prompt += "Provide an overall assessment of user's journey, considering efficiency and environmental impact based on the kilogram of CO2 emitted from using the transportation modes. Do not include infrastructure recommendations for improvement but include how can the user emit less emission by providing alternative routes or modes of transportation. Also present the kg of co2 emitted using the modes of transportation in a clean format followed by the feedback"

    # Call Gemini AI
    model = genai.GenerativeModel('gemini-2.0-flash-lite-001')
    response = model.generate_content(prompt)

    return response.text

# def main():
#     print("\n=== Transit Route Analysis ===")
#     print("Please enter the addresses for your journey:")
    
#     # Get user input for addresses
#     origin_address = input("\nEnter origin address: ").strip()
#     destination_address = input("Enter destination address: ").strip()
    
#     print("\nCalculating route and generating analysis...")
    
#     # Get and display the route analysis
#     result = get_route_data(origin_address, destination_address)
#     print("\nAnalysis Results:")
#     print("=" * 50)
#     print(result)

