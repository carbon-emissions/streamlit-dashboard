import requests
import json
import google.generativeai as genai
from backend import *

# API KEYS
GOOGLE_MAPS_API_KEY = "AIzaSyA8pRHkAHz2Zj45d2bTFwIt3V0F1PR9kA8"
GEMINI_API_KEY = "AIzaSyAlVaddDZPEljFsSzydrz7uKrGqo69Q1uU"

# Initialize Gemini AI
genai.configure(api_key=GEMINI_API_KEY)

def get_ai_feedback(start_location, end_location, travel_data, vehicle, fuel_type=None, num_passengers=None):
    """Generates AI-based feedback using Gemini."""
    
    prompt = f"""I am building a dashboard where users will be able to enter their initial and final destinations to calculate an estimation 
            of their carbon emissions for that trip. The user will input start and end location, route data from the Google Maps API, vehicle type 
            they used, fuel type of their vehicle (only if they used a personal vehicle and not transit), and the number of passengers in that trip. 
            (Also only if a personal vehicle is used). I am estimating the emissions myself using my own model, so do not include that. 
            I need you to give them recommendations based on the above information to reduce their emissions. 

            Give an overview of the trip, and then three actionable recommendations in bullet point format.
            If walking is included, do NOT give estimates of the walking distance.

            Passenger, Minivan and SUV vehicle type indicate that the user is driving.

            The user is likely going to be in the Metro Vancouver region. Based on this information, and the start and end locations,
            if you are making suggestions about alternative modes of transit (Bus etc.), try to mention which bus routes you are talking
            about.

            Do not give any overall headers. The output should have only three sections: Trip Overview and Recommendations to Reduce Carbon 
            Emissions. The headers should be in bold.

            Do not include recommendations that are not applicable to that trip For example, if user is already using transit, do not recommend
            using transit again. Also, do not say that what they are doing is a good choice. They need new recommendations only.

            The output will be directly shown on the dashboard. Refer to the user as if you are speaking to someone, and don't call them the 
            user.

            The information is given below: 
            Start location: {start_location}
            End location: {end_location}
            Route Data: {travel_data}
            Vehicle: {vehicle}
            Fuel Type: {fuel_type}
            Number of Passengers: {num_passengers}"""
    
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

