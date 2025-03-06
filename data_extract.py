import pandas as pd
import json

def process_emissions_data(file_path):
    data = pd.read_csv(file_path, low_memory=False)
    df = data.iloc[:, :-1]  # Dropping last empty column
    df.loc[df['Fuel Type'].str.startswith('ZEV', na=False), 'Fuel Type'] = 'ZEV'

    required_vehicle_types = ['Passenger', 'SUV', 'Minivan']
    bc_transport = df[df['Vehicle Type'].isin(required_vehicle_types)].reset_index(drop=True)

    bc_transport['emissions(g)'] = bc_transport['Emissions tCO2e'] * 1000 * 1000
    bc_transport['Emissions/km(g)'] = bc_transport['emissions(g)'] / bc_transport['Vehicle Kilometres Travelled']

    bc_transport_grouped = bc_transport.groupby(['Vehicle Type', 'Fuel Type'], as_index=False)['Emissions/km(g)'].mean().reset_index(drop=True)

    # Extract emissions/km for 'Passenger' vehicle type and 'Gasoline' fuel
    passenger_gasoline_emissions = bc_transport_grouped[(bc_transport_grouped['Vehicle Type'] == 'Passenger') & 
                                                        (bc_transport_grouped['Fuel Type'] == 'Gasoline')]['Emissions/km(g)'].values[0]

    # Calculate emissions for Bus and Subway based on the given ratios
    bus_emissions = (400 / 2300) * passenger_gasoline_emissions
    subway_emissions = (10 / 2300) * passenger_gasoline_emissions

    # Add Bus and Subway to the dataframe
    new_rows = [
        {'Vehicle Type': 'Bus', 'Fuel Type': None, 'Emissions/km(g)': bus_emissions},
        {'Vehicle Type': 'Subway', 'Fuel Type': None, 'Emissions/km(g)': subway_emissions}
    ]
    new_rows = pd.DataFrame(new_rows)
    bc_transport_grouped = pd.concat([bc_transport_grouped, new_rows], ignore_index=True)

    # Convert to dictionary
    data_dict = bc_transport_grouped.to_dict(orient='records')

    # Save to a JSON file
    with open('data/emissions_data.json', 'w') as f:
        json.dump(data_dict, f, indent=4)

    return data_dict

result = process_emissions_data("data/bc_transport.csv")
print(result)