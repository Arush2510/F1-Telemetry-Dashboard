import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from scripts.telemetry_utils import get_session_data, get_telemetry_for_driver
import fastf1
import numpy as np
import pandas as pd

# Enable caching
fastf1.Cache.enable_cache('C:/Users/Lenovo/Desktop/F1-Telemetry-Dashboard/data')

st.set_page_config(layout="wide")

# --- Sleek Top Bar with Driver Images ---
driver_images = ["NOR","PIA","LEC","HAM","RUS","ANT","VER","TSU","ALB","SAI","LAW","HAD","OCO","BEA","STR","ALO","HUL","BOR","GAS","COL"]

# Render sleek top bar with Streamlit layout
with st.container():
    st.markdown("""
        <div style="background-color:#0c0c0c; padding:10px; display:flex; align-items:center; border-bottom:2px solid #444;">
            <div style="display:flex; flex-wrap:nowrap; overflow-x:auto;">
    """, unsafe_allow_html=True)

    cols = st.columns(len(driver_images) + 1)
    for i, code in enumerate(driver_images):
        with cols[i]:
            st.image(f"C:/Users/Lenovo/Desktop/F1-Telemetry-Dashboard/assets/{code}.jpeg", width=40, caption=code)

    with cols[-1]:
        st.markdown("<h4 style='color:white; margin-top:20px;'></h4>", unsafe_allow_html=True)

    st.markdown("</div></div>", unsafe_allow_html=True)

st.title("F1 Live Telemetry Dashboard")

# --- User Inputs: Year, GP, Session ---
year = st.selectbox("Select Year", [2022, 2023, 2024])

# Dynamically get GPs for the selected year
schedule = fastf1.get_event_schedule(year)
gp_options = schedule['EventName'].tolist()
gp = st.selectbox("Select Grand Prix", gp_options)

session_type = st.selectbox("Session Type", ["Race", "Qualifying"])

# Load session and get dynamic driver list
session = get_session_data(year, gp, session_type)
session.load()

all_drivers = session.drivers
driver_names = [session.get_driver(d)["Abbreviation"] for d in all_drivers]
driver_names = sorted(list(set(driver_names)))

# --- Select Drivers ---
col1, col2 = st.columns(2)
with col1:
    driver1 = st.selectbox("Select Driver 1", driver_names, key="driver1")
with col2:
    driver2 = st.selectbox("Select Driver 2", driver_names, key="driver2")

# --- Load Telemetry ---
if st.button("Load Telemetry"):
    telemetry1 = get_telemetry_for_driver(session, driver1)
    telemetry2 = get_telemetry_for_driver(session, driver2)

    st.success(f"Loaded telemetry for {driver1} and {driver2} - {gp} {year} [{session_type}]")

    # --- Fastest Laps ---
    driver_laps1 = session.laps.pick_driver(driver1)
    fastest_lap1 = driver_laps1.pick_fastest()

    driver_laps2 = session.laps.pick_driver(driver2)
    fastest_lap2 = driver_laps2.pick_fastest()

    st.header("📊 Driver Session Summary")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader(driver1)
        st.metric("Fastest Lap Time", str(fastest_lap1['LapTime']))
        st.metric("Avg Speed (kph)", f"{fastest_lap1.get('SpeedST', 'N/A'):.1f}" if 'SpeedST' in fastest_lap1 else "N/A")
        st.metric("Tire", fastest_lap1['Compound'])

    with col2:
        st.subheader(driver2)
        st.metric("Fastest Lap Time", str(fastest_lap2['LapTime']))
        st.metric("Avg Speed (kph)", f"{fastest_lap2.get('SpeedST', 'N/A'):.1f}" if 'SpeedST' in fastest_lap2 else "N/A")
        st.metric("Tire", fastest_lap2['Compound'])

    # --- Sector Breakdown (Driver 1) ---
    st.subheader(f"📏 Sector Breakdown - {driver1}")
    sector_data1 = {
        "Sector": ["Sector 1", "Sector 2", "Sector 3"],
        "Time": [
            str(fastest_lap1['Sector1Time']),
            str(fastest_lap1['Sector2Time']),
            str(fastest_lap1['Sector3Time'])
        ],
        "Compound": [fastest_lap1['Compound']] * 3
    }

    try:
        sector_speeds1 = [
            telemetry1[telemetry1['Distance'] <= fastest_lap1['Sector1Distance']]['Speed'].mean(),
            telemetry1[(telemetry1['Distance'] > fastest_lap1['Sector1Distance']) &
                       (telemetry1['Distance'] <= fastest_lap1['Sector2Distance'])]['Speed'].mean(),
            telemetry1[telemetry1['Distance'] > fastest_lap1['Sector2Distance']]['Speed'].mean()
        ]
        sector_data1["Avg Speed (kph)"] = [f"{s:.1f}" for s in sector_speeds1]
    except:
        sector_data1["Avg Speed (kph)"] = ["N/A", "N/A", "N/A"]

    st.dataframe(pd.DataFrame(sector_data1), use_container_width=True)

    # --- Comparison Charts ---
    def plot_comparison(title, y_label, field):
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=telemetry1['Distance'], y=telemetry1[field],
                                 mode='lines', name=driver1, line=dict(color='red')))
        fig.add_trace(go.Scatter(x=telemetry2['Distance'], y=telemetry2[field],
                                 mode='lines', name=driver2, line=dict(color='blue')))
        fig.update_layout(title=title, xaxis_title='Distance', yaxis_title=y_label)
        st.plotly_chart(fig, use_container_width=True)

    plot_comparison("Speed vs Distance", "Speed (kph)", "Speed")
    plot_comparison("Throttle % vs Distance", "Throttle", "Throttle")
    plot_comparison("Brake % vs Distance", "Brake", "Brake")
    plot_comparison("RPM vs Distance", "RPM", "RPM")

    # --- Track Map Comparison ---
    fig_map = go.Figure()
    fig_map.add_trace(go.Scatter(
        x=telemetry1['X'], y=telemetry1['Y'],
        mode='lines', line=dict(color='red', width=3),
        name=f"{driver1} Racing Line"
    ))
    fig_map.add_trace(go.Scatter(
        x=telemetry2['X'], y=telemetry2['Y'],
        mode='lines', line=dict(color='blue', width=3),
        name=f"{driver2} Racing Line"
    ))
    fig_map.update_layout(
        title='Track Map Comparison',
        xaxis_title='X', yaxis_title='Y',
        height=600
    )
    st.plotly_chart(fig_map, use_container_width=True)

    # --- Lap Playback Animation (Driver 1) ---
    st.subheader(f"🏁 Lap Playback - {driver1}")
    telemetry_anim = telemetry1.iloc[::10]
    if not telemetry_anim.empty:
        fig_anim = go.Figure()

        # Background track
        fig_anim.add_trace(go.Scatter(
            x=telemetry1['X'],
            y=telemetry1['Y'],
            mode='lines',
            line=dict(color='lightgray', width=2),
            name='Track Layout'
        ))

        # Driver marker
        fig_anim.add_trace(go.Scatter(
            x=[telemetry_anim.iloc[0]['X']],
            y=[telemetry_anim.iloc[0]['Y']],
            mode='markers',
            marker=dict(size=12, color='red'),
            name=driver1
        ))

        # Frames
        frames = []
        for i in range(len(telemetry_anim)):
            frames.append(go.Frame(
                data=[
                    go.Scatter(
                        x=telemetry1['X'],
                        y=telemetry1['Y'],
                        mode='lines',
                        line=dict(color='lightgray', width=2)
                    ),
                    go.Scatter(
                        x=[telemetry_anim.iloc[i]['X']],
                        y=[telemetry_anim.iloc[i]['Y']],
                        mode='markers',
                        marker=dict(size=12, color='red')
                    )
                ],
                name=str(i)
            ))

        fig_anim.frames = frames
        fig_anim.update_layout(
            title='Lap Playback Animation',
            xaxis_title='X',
            yaxis_title='Y',
            height=600,
            updatemenus=[
                {
                    "type": "buttons",
                    "buttons": [
                        {"label": "Play", "method": "animate",
                         "args": [None, {"frame": {"duration": 40, "redraw": True}, "fromcurrent": True}]},
                        {"label": "Pause", "method": "animate",
                         "args": [[None], {"frame": {"duration": 0, "redraw": False}, "mode": "immediate"}]}
                    ],
                    "showactive": False
                }
            ]
        )
        st.plotly_chart(fig_anim, use_container_width=True)
