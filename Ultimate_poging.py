# %%
import requests
import pandas as pd
import streamlit as st
from folium.features import CustomIcon
from streamlit_folium import st_folium  # Import this for Folium integration
import folium
from datetime import datetime


# %%
api_key = 'd5184c3b4e'
cities = [
    'Assen', 'Lelystad', 'Leeuwarden', 'Arnhem', 'Groningen', 'Maastricht', 
    'Eindhoven', 'Den Helder', 'Enschede', 'Amersfoort', 'Middelburg', 'Rotterdam'
]
liveweer = []
wk_verw = []
uur_verw = []
api_data = []

# %%
for city in cities:
    api_url = f'https://weerlive.nl/api/weerlive_api_v2.php?key={api_key}&locatie={city}'
    response = requests.get(api_url)

    if response.status_code == 200:
        data = response.json()
        if 'liveweer' in data:
            liveweer.extend(data['liveweer'])
        if 'wk_verw' in data:
            for entry in data['wk_verw']:
                entry['plaats'] = city
            wk_verw.extend(data['wk_verw'])
        if 'uur_verw' in data:
            for entry in data['uur_verw']:
                entry['plaats'] = city
            uur_verw.extend(data['uur_verw'])
        if 'api_data' in data:
            api_data.extend(data['api'])

    else:
        print(f"Error fetching data for {city}: {response.status_code}")

df_liveweer = pd.DataFrame(liveweer)
df_wk_verw = pd.DataFrame(wk_verw)
df_uur_verw = pd.DataFrame(uur_verw)
df_api_data = pd.DataFrame(api_data)

# %%
df_uur_verw.head(15)

# %%
# en 'timestamp' is een Unix time in seconden.
df_uur_verw['datetime'] = pd.to_datetime(df_uur_verw['timestamp'], unit='s')

# Vervolgens kun je twee nieuwe kolommen maken: "datum" en "uur".
df_uur_verw['datum'] = df_uur_verw['datetime'].dt.strftime('%d-%m-%Y')
df_uur_verw['uur']   = df_uur_verw['datetime'].dt.strftime('%H:%M:%S')

# Eventueel kun je daarna de hulpkolom weer weggooien:
# df_uur_verw.drop(columns='datetime', inplace=True)

df_uur_verw.head()

# %%
# Stap 3: Zet "uur" om naar een datetime.time
df_uur_verw['uur'] = pd.to_datetime(df_uur_verw['uur'], errors='coerce')
print(df_uur_verw.dtypes)

# %%

# Weather condition to icon mapping
weather_icons = {
    "zonnig": "zonnig.png",
    "bewolkt": "bewolkt.png",
    "half bewolkt": "halfbewolkt.png",
    "licht bewolkt": "halfbewolkt.png",
    "regen": "regen.png",
    "buien": "buien.png",
    "mist": "mist.png",
    "sneeuw": "sneeuw.png",
    "onweer": "bliksem.png",
    "hagel": "hagel.png",
    "heldere nacht": "helderenacht.png",
    "nachtmist": "nachtmist.png",
    "wolkennacht": "wolkennacht.png",
    "zwaar bewolkt": "zwaarbewolkt.png"
}

# City coordinates for icon placements (ensure this is updated for your cities)
city_coords = {
    "Assen": [52.9929, 6.5642],
    "Lelystad": [52.5185, 5.4714],
    "Leeuwarden": [53.2012, 5.7999],
    "Arnhem": [51.9851, 5.8987],
    "Groningen": [53.2194, 6.5665],
    "Maastricht": [50.8514, 5.6910],
    "Eindhoven": [51.4416, 5.4697],
    "Den Helder": [52.9563, 4.7601],
    "Enschede": [52.2215, 6.8937],
    "Amersfoort": [52.1561, 5.3878],
    "Middelburg": [51.4988, 3.6136],
    "Rotterdam": [51.9225, 4.4792],
}

# Add lat/lon to df_liveweer
df_liveweer["lat"] = df_liveweer["plaats"].map(lambda city: city_coords.get(city, [None, None])[0])
df_liveweer["lon"] = df_liveweer["plaats"].map(lambda city: city_coords.get(city, [None, None])[1])

# Streamlit widgets to allow the user to choose visualization type
visualization_option = st.selectbox("Select the visualization type", ["Temperature", "Weather"])

# Create the map based on selected visualization
def create_map(df_liveweer, visualization_option):
    nl_map = folium.Map(location=[52.3, 5.3], zoom_start=8)

    for index, row in df_liveweer.iterrows():
        if visualization_option == "Weather":
            weather_desc = row['samenv'].lower()
            icon_file = weather_icons.get(weather_desc, "bewolkt.png")  # Default icon for weather
            icon_path = f"iconen-weerlive/{icon_file}"
            
            popup_text = f"{row['plaats']}: {row['temp']}°C, {row['samenv']}"
            
            folium.Marker(
                location=[row["lat"], row["lon"]],
                popup=popup_text,
                tooltip=row["plaats"],
                icon=CustomIcon(icon_path, icon_size=(30, 30))
            ).add_to(nl_map)

        elif visualization_option == "Temperature":
            temp_popup = f"Temperature: {row['temp']}°C"
            
            folium.Marker(
                location=[row["lat"], row["lon"]],
                popup=temp_popup,
                tooltip=row["plaats"]
            ).add_to(nl_map)

    return nl_map

# Create the map based on the dropdown selection
nl_map = create_map(df_liveweer, visualization_option)

# Display the map in Streamlit
st_folium(nl_map, width=700)  # Adjust width as needed

# Optionally: You can add more visualizations or data below (such as graphs, tables, etc.)
# %%

# %%



