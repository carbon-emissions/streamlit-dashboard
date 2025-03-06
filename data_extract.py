import pandas as pd
import json

data = pd.read_csv("data/bc_transport.csv", low_memory=False)
df = data.iloc[:, :-1] # Dropping last empty column
df.loc[df['Fuel Type'].str.startswith('ZEV', na=False), 'Fuel Type'] = 'ZEV'

required_vehicle_types = ['Passenger', 'SUV', 'Minivan']

bc_transport = df[df['Vehicle Type'].isin(required_vehicle_types)].reset_index(drop=True)

bc_transport['emissions(g)'] = bc_transport['Emissions tCO2e']*1000*1000
bc_transport['Emissions/km(g)'] = bc_transport['emissions(g)']/bc_transport['Vehicle Kilometres Travelled']

bc_transport_grouped = bc_transport.groupby(['Vehicle Type', 'Fuel Type'], as_index=False)['Emissions/km(g)'].mean().reset_index(drop=True)

data_dict = bc_transport_grouped.to_dict(orient='records')

# Save to a JSON file
import json
with open('data/emissions_data.json', 'w') as f:
    json.dump(data_dict, f, indent=4)