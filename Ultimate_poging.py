# -----------------------------------------------------------------------------
# 2) Build the map & chart
# -----------------------------------------------------------------------------
df_selected_cities = df_uur_verw[df_uur_verw['plaats'].isin(selected_cities)]
visualization_option = st.selectbox(
    "Selecteer weergave", 
    ["Temperatuur", "Weer", "Neerslag"]
)

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

nl_map = create_full_map(df_uur_verw, visualization_option, selected_hour, selected_cities)
st_folium(nl_map, width=700)

if len(selected_cities) == 0:
    st.warning("Geen stad geselecteerd. Kies een stad onderaan de pagina om de grafiek te tonen.")
else:
    if visualization_option in ["Temperatuur", "Neerslag"]:
        # ---------------------------------------------------------------------
        # Theming for a weather-style chart
        # ---------------------------------------------------------------------
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
                city_data = df_selected_cities[df_selected_cities['plaats'] == city].sort_values('tijd')
                city_data['temp'] = city_data['temp'].interpolate(method='linear')

                ax1.set_xlabel('Tijd')
                ax1.set_ylabel('Temperatuur (°C)', color='tab:red')
                ax1.plot(city_data['tijd'], city_data['temp'], label=city, linestyle='-', marker='o')

            ax1.tick_params(axis='y', labelcolor='tab:red')
            ax1.set_title("Temperatuur per Stad")

        elif visualization_option == "Neerslag":
            for city in selected_cities:
                city_data = df_selected_cities[df_selected_cities['plaats'] == city].sort_values('tijd')
                city_data['neersl'] = city_data['neersl'].interpolate(method='linear')
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

        # Hourly ticks, rotated labels:
        ax1.xaxis.set_major_locator(mdates.HourLocator(interval=1))
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        plt.setp(ax1.get_xticklabels(), rotation=45, ha="right")

        fig.legend(loc='upper right', bbox_to_anchor=(1.1, 1), bbox_transform=ax1.transAxes)
        plt.tight_layout()
        st.pyplot(fig)

# -----------------------------------------------------------------------------
# 3) Show or hide checkboxes
# -----------------------------------------------------------------------------
if visualization_option != "Weer":
    st.subheader("Selecteer steden (onderaan)")
    st.write("Hieronder kun je de steden aanpassen. Standaard is alleen de eerste stad geselecteerd.")
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
