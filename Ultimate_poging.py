import requests
import pandas as pd
import streamlit as st
from folium.features import CustomIcon
from streamlit_folium import st_folium  # Import this for Folium integration
import folium
from datetime import datetime, timedelta

# API Configuratie
api_key = 'd5184c3b4e'
cities = [
    'Assen', 'Lelystad', 'Leeuwarden', 'Arnhem', 'Groningen', 'Maastricht', 
    'Eindhoven', 'Den Helder', 'Enschede', 'Amersfoort', 'Middelburg', 'Rotterdam'
]
liveweer = []
wk_verw = []
uur_verw = []
api_data = []

# Data ophalen van API
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

# Dataframes aanmaken
df_liveweer = pd.DataFrame(liveweer)
df_wk_verw = pd.DataFrame(wk_verw)
df_uur_verw = pd.DataFrame(uur_verw)
df_api_data = pd.DataFrame(api_data)

# Tijd omzetten
df_uur_verw['datetime'] = pd.to_datetime(df_uur_verw['timestamp'], unit='s')
df_uur_verw['datum'] = df_uur_verw['datetime'].dt.strftime('%d-%m-%Y')
df_uur_verw['tijd'] = df_uur_verw['datetime'].dt.strftime('%H:%M')
df_uur_verw['tijd'] = pd.to_datetime(df_uur_verw['tijd'], format='%H:%M', errors='coerce')

# Verwijder rijen met ontbrekende coördinaten
df_uur_verw.dropna(subset=["lat", "lon"], inplace=True)

# Streamlit UI
st.title("Weerkaart Nederland")

# Weericoon mapping
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

# Stad coordinaten
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

# Voeg lat/lon toe aan df_uur_verw
df_uur_verw["lat"] = df_uur_verw["plaats"].map(lambda city: city_coords.get(city, [None, None])[0])
df_uur_verw["lon"] = df_uur_verw["plaats"].map(lambda city: city_coords.get(city, [None, None])[1])

# Selectie van de visualisatietype
visualization_option = st.selectbox("Selecteer de visualisatie", ["Temperature", "Weather"])

def create_map(df, visualisatie_optie):
    nl_map = folium.Map(location=[52.3, 5.3], zoom_start=8)
    for index, row in df.iterrows():
        if pd.notna(row["lat"]) and pd.notna(row["lon"]):
            if visualisatie_optie == "Weather":
                icon_file = weather_icons.get(row['image'].lower(), "bewolkt.png")
                icon_path = f"iconen-weerlive/{icon_file}"
                popup_text = f"{row['plaats']}"
                folium.Marker(
                    location=[row["lat"], row["lon"]],
                    popup=popup_text,
                    tooltip=row["plaats"],
                    icon=CustomIcon(icon_path, icon_size=(30, 30))
                ).add_to(nl_map)
            elif visualisatie_optie == "Temperature":
                if not pd.isna(row['temp']):
                    temp_popup = f"{row['plaats']}"
                    folium.Marker(
                        location=[row["lat"], row["lon"]],
                        popup=temp_popup,
                        tooltip=row["plaats"],
                        icon=folium.DivIcon(html=f'<div style="font-size: 12pt; font-weight: bold; color: red;">{row["temp"]}°C</div>')
                    ).add_to(nl_map)
    return nl_map

# Maak en toon de kaart
nl_map = create_map(df_uur_verw, visualization_option)
st_folium(nl_map, width=700)
