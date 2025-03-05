import json

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

# Example usage:
vehicle_type = 'Minivan'
fuel_type = 'Gasoline'
total_km = 10 
num_passengers = 4  # optional

emissions = calculate_emissions(vehicle_type, fuel_type, total_km, num_passengers)
print(f"Emissions per passenger: {emissions} grams")
