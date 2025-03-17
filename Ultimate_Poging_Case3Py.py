# %%
import streamlit as st
import folium
from streamlit_folium import folium_static
import pandas as pd

bestanden = [
    '2021 Q2 spring (Apr-Jun)-Central.csv',
    '2021 Q3 (Jul-Sep)-Central.csv',
    '2021 Q4 autumn (Oct-Dec)-Central.csv'
]

dfs = [pd.read_csv(file) for file in bestanden]

fiets_data_jaar = pd.concat(dfs, ignore_index=True)
weer_data = pd.read_csv('weather_london.csv')
metro_data = pd.read_csv('AC2021_AnnualisedEntryExit.csv', sep = ';')
metro_stations_data = pd.read_csv('London stations.csv')

# Dictionary of { "StationName": (latitude, longitude) }
stations_dict = {
    row["Station"]: (row["Latitude"], row["Longitude"]) 
    for _, row in metro_stations_data.iterrows()
}

m = folium.Map(location=[51.509865, -0.118092], zoom_start=11)

# Loop through every station in AC2021_AnnualisedEntryExit
for idx, row in metro_data.iterrows():
    station_name = row["Station"]  # Adjust if your CSV column is named differently
    
    # Convert busy_value to a numeric type to avoid the string/int error
    busy_value = pd.to_numeric(row["AnnualisedEnEx"], errors="coerce")

    # Check if station exists in the dictionary to avoid KeyErrors
    if station_name in stations_dict:
        lat, lon = stations_dict[station_name]
        
        # Scale factor for the circle radius
        scale_factor = 1000000
        radius = busy_value / scale_factor if pd.notnull(busy_value) else 2
        
        folium.CircleMarker(
            location=[lat, lon],
            radius=radius,
            popup=f"{station_name}: {busy_value:,}" if pd.notnull(busy_value) else station_name,
            fill=True,
            fill_opacity=0.6
        ).add_to(m)

folium_static(m)



