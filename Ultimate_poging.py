import requests
import pandas as pd
import streamlit as st
from folium.features import CustomIcon
from streamlit_folium import st_folium  # Import this for Folium integration
import folium
import matplotlib.pyplot as plt  # For graphing
from datetime import datetime
import numpy as np
import matplotlib.dates as mdates  # For date/time on the x-axis

# API Configuration
api_key = 'd5184c3b4e'
cities = [
    'Assen', 'Lelystad', 'Leeuwarden', 'Arnhem', 'Groningen', 'Maastricht',
    'Eindhoven', 'Den Helder', 'Enschede', 'Amersfoort', 'Middelburg', 'Rotterdam'
]

@st.cache_data
def fetch_weather_data():
    liveweer, wk_verw, uur_verw, api_data = [], [], [], []
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
    return liveweer, wk_verw, uur_verw, api_data

liveweer, wk_verw, uur_verw, api_data = fetch_weather_data()

df_liveweer = pd.DataFrame(liveweer)
df_wk_verw = pd.DataFrame(wk_verw)
df_uur_verw = pd.DataFrame(uur_verw)
df_api_data = pd.DataFrame(api_data)

@st.cache_data
def process_hourly_data(df):
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
    df['datum'] = df['datetime'].dt.strftime('%d-%m-%Y')
    df['tijd'] = df['datetime'].dt.strftime('%H:%M')
    df['tijd'] = pd.to_datetime(df['tijd'], format='%H:%M', errors='coerce')
    return df

df_uur_verw = process_hourly_data(df_uur_verw)

st.title("Weerkaart Nederland")

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

df_uur_verw["lat"] = df_uur_verw["plaats"].map(lambda city: city_coords.get(city, [None, None])[0])
df_uur_verw["lon"] = df_uur_verw["plaats"].map(lambda city: city_coords.get(city, [None, None])[1])

@st.cache_data
def create_full_map(df, visualisatie_optie, geselecteerde_uur):
    nl_map = folium.Map(location=[52.3, 5.3], zoom_start=8)
    df_filtered = df[df["tijd"] == geselecteerde_uur]

    for index, row in df_filtered.iterrows():
        if visualisatie_optie == "Weather":
            icon_file = weather_icons.get(row['image'].lower(), "bewolkt.png")
            icon_path = f"iconen-weerlive/{icon_file}"
            popup_text = f"{row['plaats']}: {row['temp']}°C, {row['image']}"
            
            folium.Marker(
                location=[row["lat"], row["lon"]],
                popup=popup_text,
                tooltip=row["plaats"],
                icon=CustomIcon(icon_path, icon_size=(30, 30))
            ).add_to(nl_map)

        elif visualisatie_optie == "Temperature":
            # Updated styling for the temperature
            folium.map.Marker(
                location=[row["lat"], row["lon"]],
                tooltip=row["plaats"],
                icon=folium.DivIcon(
                    html=(
                        '<div style="'
                        'display:inline-block;'
                        'white-space:nowrap;'
                        'line-height:1;'                           # ensure minimal height
                        'background-color: rgba(255, 255, 255, 0.7);'
                        'border: 1px solid red;'
                        'border-radius: 4px;'
                        'padding: 2px 6px;'                        # tweak padding to taste
                        'color: red;'
                        'font-weight: bold;'
                        'font-size:18px;'
                        'text-align:center;'
                        '">'
                        f'{row["temp"]}°C'
                        '</div>'
                    )
                )
            ).add_to(nl_map)

        elif visualisatie_optie == "Precipitation":
            folium.map.Marker(
                location=[row["lat"], row["lon"]],
                tooltip=row["plaats"],
                icon=folium.DivIcon(
                    html=f'<div style="color:blue; font-weight:bold; font-size:18px;">{row["neersl"]} mm</div>'
                )
            ).add_to(nl_map)

    return nl_map

selected_cities = []

st.subheader("Selecteer steden:")
cols = st.columns(3)
for i, city in enumerate(cities):
    with cols[i % 3]:
        checkbox_key = f"checkbox_{city}_{i}"
        if st.checkbox(city, value=True, key=checkbox_key):
            selected_cities.append(city)

if not selected_cities:
    st.warning("Selecteer minstens één stad om het weer te bekijken.")

df_selected_cities = df_uur_verw[df_uur_verw['plaats'].isin(selected_cities)]
visualization_option = st.selectbox("Selecteer weergave", ["Temperature", "Weather", "Precipitation"])

unieke_tijden = df_selected_cities["tijd"].dropna().unique()
huidig_uur = datetime.now().replace(minute=0, second=0, microsecond=0)
if huidig_uur not in unieke_tijden and len(unieke_tijden) > 0:
    huidig_uur = unieke_tijden[0]
selected_hour = st.select_slider(
    "Selecteer uur",
    options=sorted(unieke_tijden),
    value=huidig_uur,
    format_func=lambda t: t.strftime('%H:%M') if not pd.isnull(t) else "No time"
)

nl_map = create_full_map(df_uur_verw, visualization_option, selected_hour)
st_folium(nl_map, width=700)

if selected_cities and visualization_option in ["Temperature", "Precipitation"]:
    fig, ax1 = plt.subplots(figsize=(10, 5))

    if visualization_option == "Temperature":
        for city in selected_cities:
            city_data = df_selected_cities[df_selected_cities['plaats'] == city]
            city_data = city_data.sort_values('tijd')

            city_data['temp'] = city_data['temp'].interpolate(method='linear')

            ax1.set_xlabel('Tijd')
            ax1.set_ylabel('Temperatuur (°C)', color='tab:red')
            ax1.plot(city_data['tijd'], city_data['temp'], label=city, linestyle='-', marker='o')

        ax1.tick_params(axis='y', labelcolor='tab:red')

    elif visualization_option == "Precipitation":
        for city in selected_cities:
            city_data = df_selected_cities[df_selected_cities['plaats'] == city]
            city_data = city_data.sort_values('tijd')

            city_data['neersl'] = city_data['neersl'].interpolate(method='linear')
            if city_data['neersl'].isna().all():
                city_data['neersl'] = 0

            ax1.set_xlabel('Tijd')
            ax1.set_ylabel('Neerslag (mm)', color='tab:blue')
            ax1.plot(city_data['tijd'], city_data['neersl'], label=city, linestyle='-', marker='x')

        ax1.set_ylim(-0.2, 8)
        ax1.set_yticks(range(0, 9))
        ax1.tick_params(axis='y', labelcolor='tab:blue')

    ax1.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))

    plt.title(f"{visualization_option} Comparison")
    fig.legend(loc='upper right', bbox_to_anchor=(1.1, 1), bbox_transform=ax1.transAxes)
    plt.tight_layout()
    st.pyplot(fig)
