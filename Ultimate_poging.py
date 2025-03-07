import requests
import pandas as pd
import streamlit as st
from folium.features import CustomIcon
from streamlit_folium import st_folium
import folium
import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np
import matplotlib.dates as mdates

# --- API Configuration ---
api_key = 'd5184c3b4e'
cities = [
    'Assen', 'Lelystad', 'Leeuwarden', 'Arnhem', 'Groningen', 'Maastricht',
    'Eindhoven', 'Den Helder', 'Enschede', 'Amersfoort', 'Middelburg', 'Rotterdam'
]

# --- Data ophalen en cachen ---
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

# --- Uur-data verwerken ---
@st.cache_data
def process_hourly_data(df):
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
    df['datum'] = df['datetime'].dt.strftime('%d-%m-%Y')
    df['tijd'] = df['datetime'].dt.strftime('%H:%M')
    df['tijd'] = pd.to_datetime(df['tijd'], format='%H:%M', errors='coerce')
    return df

df_uur_verw = process_hourly_data(df_uur_verw)

# --- Title ---
st.title("Het weer van vandaag")

# --- Sessie-state voor geselecteerde steden ---
if "selected_cities" not in st.session_state:
    # Standaard minstens 1 stad geselecteerd
    st.session_state["selected_cities"] = [cities[0]]

# We halen hier de selectie uit de session_state.
selected_cities = st.session_state["selected_cities"]

# --- Kaart-iconen en coördinaten ---
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

def create_full_map(df, visualisatie_optie, geselecteerde_uur):
    nl_map = folium.Map(location=[52.3, 5.3], zoom_start=8)
    df_filtered = df[df["tijd"] == geselecteerde_uur]

    for _, row in df_filtered.iterrows():
        if visualisatie_optie == "Weer":
            icon_file = weather_icons.get(str(row['image']).lower(), "bewolkt.png")
            icon_path = f"iconen-weerlive/{icon_file}"
            popup_text = f"{row['plaats']}: {row['temp']}°C, {row['image']}"
            
            folium.Marker(
                location=[row["lat"], row["lon"]],
                popup=popup_text,
                tooltip=row["plaats"],
                icon=CustomIcon(icon_path, icon_size=(30, 30))
            ).add_to(nl_map)

        elif visualisatie_optie == "Temperatuur":
            folium.Marker(
                location=[row["lat"], row["lon"]],
                tooltip=row["plaats"],
                icon=folium.DivIcon(
                    html=(
                        '<div style="'
                        'display:inline-block;'
                        'white-space:nowrap;'
                        'line-height:1;'
                        'background-color: rgba(255, 255, 255, 0.7);'
                        'border: 1px solid red;'
                        'border-radius: 4px;'
                        'padding: 2px 6px;'
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

        elif visualisatie_optie == "Neerslag":
            folium.Marker(
                location=[row["lat"], row["lon"]],
                tooltip=row["plaats"],
                icon=folium.DivIcon(
                    html=(
                        '<div style="'
                        'display:inline-block;'
                        'white-space:nowrap;'
                        'line-height:1;'
                        'background-color: rgba(255, 255, 255, 0.7);'
                        'border: 1px solid blue;'
                        'border-radius: 4px;'
                        'padding: 2px 6px;'
                        'color: blue;'
                        'font-weight: bold;'
                        'font-size:18px;'
                        'text-align:center;'
                        '">'
                        f'{row["neersl"]} mm'
                        '</div>'
                    )
                )
            ).add_to(nl_map)

    return nl_map

# ----------------------------------
# 1. Data filteren op basis van de sessie-state
# ----------------------------------
df_selected_cities = df_uur_verw[df_uur_verw['plaats'].isin(selected_cities)]

# ----------------------------------
# 2. Selecties voor visualisatie (kaarten/grafiek)
# ----------------------------------
visualization_option = st.selectbox("Selecteer weergave", ["Temperatuur", "Weer", "Neerslag"])

# Bepaal welke tijden beschikbaar zijn voor de (eventuele) slider
unieke_tijden = df_selected_cities["tijd"].dropna().unique()

# Zorg dat de "standaard uur" bestaat of neem de eerste uit unieke_tijden
huidig_uur = datetime.now().replace(minute=0, second=0, microsecond=0)
if huidig_uur not in unieke_tijden and len(unieke_tijden) > 0:
    huidig_uur = unieke_tijden[0]

selected_hour = None
if len(unieke_tijden) > 0:
    selected_hour = st.select_slider(
        "Selecteer uur",
        options=sorted(unieke_tijden),
        value=huidig_uur,
        format_func=lambda t: t.strftime('%H:%M') if not pd.isnull(t) else "No time"
    )
else:
    st.warning("Er zijn geen tijden beschikbaar (geen steden geselecteerd of geen data).")

# ----------------------------------
# 3. Kaart tonen
# ----------------------------------
if selected_hour is not None:
    nl_map = create_full_map(df_selected_cities, visualization_option, selected_hour)
    st_folium(nl_map, width=700)

# ----------------------------------
# 4. Grafiek tonen (indien geen 'Weer' en er is ten minste 1 stad)
# ----------------------------------
if len(selected_cities) == 0:
    st.warning("Geen stad geselecteerd. Kies een stad onderaan de pagina om de grafiek te tonen.")
else:
    if visualization_option in ["Temperatuur", "Neerslag"] and selected_hour is not None:
        plt.rcParams['axes.facecolor'] = '#f0f8ff'
        plt.rcParams['figure.facecolor'] = '#f0f8ff'
        plt.rcParams['axes.edgecolor'] = '#b0c4de'
        plt.rcParams['axes.labelcolor'] = '#333333'
        plt.rcParams['xtick.color'] = '#333333'
        plt.rcParams['ytick.color'] = '#333333'
        plt.rcParams['grid.color'] = '#b0c4de'
        plt.rcParams['grid.linestyle'] = '--'
        plt.rcParams['grid.linewidth'] = 0.5
        plt.rcParams['axes.titlepad'] = 15

        fig, ax1 = plt.subplots(figsize=(10, 5))

        if visualization_option == "Temperatuur":
            for city in selected_cities:
                city_data = df_selected_cities[df_selected_cities['plaats'] == city].copy()
                city_data = city_data.sort_values('tijd')
                city_data['temp'] = pd.to_numeric(city_data['temp'], errors='coerce').interpolate(method='linear')

                ax1.set_xlabel('Tijd')
                ax1.set_ylabel('Temperatuur (°C)', color='tab:red')
                ax1.plot(city_data['tijd'], city_data['temp'], label=city, linestyle='-', marker='o')

            ax1.tick_params(axis='y', labelcolor='tab:red')
            ax1.set_title("Temperatuur per Stad")

        elif visualization_option == "Neerslag":
            for city in selected_cities:
                city_data = df_selected_cities[df_selected_cities['plaats'] == city].copy()
                city_data = city_data.sort_values('tijd')
                # Neerslag kan leeg of niet numeriek zijn
                city_data['neersl'] = pd.to_numeric(city_data['neersl'], errors='coerce').interpolate(method='linear')
                # Als alles NaN is, zet op 0 om lege grafieken te voorkomen
                if city_data['neersl'].isna().all():
                    city_data['neersl'] = 0

                ax1.set_xlabel('Tijd')
                ax1.set_ylabel('Neerslag (mm)', color='tab:blue')
                ax1.plot(city_data['tijd'], city_data['neersl'], label=city, linestyle='-', marker='x')

            ax1.set_ylim(-0.2, 8)
            ax1.set_yticks(range(0, 9))
            ax1.tick_params(axis='y', labelcolor='tab:blue')
            ax1.set_title("Neerslag per Stad")

        ax1.grid(True)
        ax1.xaxis.set_major_locator(mdates.HourLocator(interval=1))
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        plt.setp(ax1.get_xticklabels(), rotation=45, ha="right")

        fig.legend(loc='upper right', bbox_to_anchor=(1.1, 1), bbox_transform=ax1.transAxes)
        plt.tight_layout()
        st.pyplot(fig)

# ----------------------------------
# 5. Checkboxes (onderaan)
# ----------------------------------
st.markdown("---")
st.subheader("Selecteer steden")
st.write("Vink hieronder de steden aan die je wilt weergeven:")

cols = st.columns(3)
for i, city in enumerate(cities):
    with cols[i % 3]:
        key = f"checkbox_{city}_{i}"
        checked_now = city in st.session_state["selected_cities"]
        checkbox_value = st.checkbox(city, value=checked_now, key=key)

        if checkbox_value and city not in st.session_state["selected_cities"]:
            st.session_state["selected_cities"].append(city)
        elif not checkbox_value and city in st.session_state["selected_cities"]:
            st.session_state["selected_cities"].remove(city)
