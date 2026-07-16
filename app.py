import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from collections import deque
from datetime import datetime
from utils.drawing import draw_earth_and_orbit
from streamlit_autorefresh import st_autorefresh


# ---------------------------------
# Page Configuration
# ---------------------------------

st.set_page_config(
    page_title="OrbitVision",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ---------------------------------
# Professional Space Theme
# ---------------------------------

st.markdown(
    """
    <style>

    .stApp {
        background-color: #050816;
        color: white;
    }

    h1 {
        color: #00e5ff;
        text-align: center;
        font-size: 45px;
    }

    h2 {
        color: #00e5ff;
    }

    h3 {
        color: white;
        text-align: center;
    }

    .stInfo {
        background-color: #111827;
        border-radius: 12px;
        border: 1px solid #00e5ff;
    }

    section[data-testid="stSidebar"] {
        background-color: #0b1120;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ---------------------------------
# Header
# ---------------------------------

st.title("🛰️ ORBITVISION")

st.markdown(
    """
    <h3>
    Satellite Mission Control & Orbit Visualization System
    </h3>
    """,
    unsafe_allow_html=True
)

st.markdown("---")


# ---------------------------------
# Automatic Satellite Animation
# ---------------------------------

count = st_autorefresh(
    interval=500,
    limit=None,
    key="orbit_animation"
)


# ---------------------------------
# Mission Timer
# ---------------------------------

if "mission_start_time" not in st.session_state:
    st.session_state.mission_start_time = datetime.now()

elapsed = datetime.now() - st.session_state.mission_start_time
total_seconds = int(elapsed.total_seconds())

hours = total_seconds // 3600
minutes = (total_seconds % 3600) // 60
seconds = total_seconds % 60

mission_time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

st.markdown(
    f"""
    <div style="text-align:center; margin-top:-10px; margin-bottom:20px;">
        <span style="color:#94a3b8; font-size:14px; letter-spacing:2px;">MISSION TIME</span><br>
        <span style="color:#00e5ff; font-size:32px; font-weight:bold; font-family:monospace;">{mission_time_str}</span>
    </div>
    """,
    unsafe_allow_html=True
)


moon_angle = (count * 1.2) % 360   # Moon moves slower than any satellite


# ---------------------------------
# Sidebar Controls
# ---------------------------------

st.sidebar.title("🛰️ Satellite Controls")

orbit_type = st.sidebar.selectbox(
    "Focus Telemetry On",
    ["LEO", "MEO", "GEO"]
)

st.sidebar.success("🟢 Automatic Orbit Tracking Enabled")
st.sidebar.info("All three satellites orbit simultaneously. Use the dropdown to choose which one's telemetry panel you're watching.")


# ---------------------------------
# Orbit Parameters (all three satellites, always defined)
# ---------------------------------
# angular_speed = degrees advanced per refresh tick. Roughly proportional
# to each orbit's real relative speed (LEO fastest, GEO slowest) so the
# animation "feels" physically right without being a literal real-time sim.

ORBITS = {
    "LEO": {
        "radius": 1.8, "altitude": "400 km", "speed": "7.66 km/s",
        "speed_kms": 7.66, "period": "90 Minutes", "mission": "Earth Observation",
        "color": "#22d3ee", "angular_speed": 5.0,
    },
    "MEO": {
        "radius": 2.3, "altitude": "20,000 km", "speed": "3.87 km/s",
        "speed_kms": 3.87, "period": "12 Hours", "mission": "Navigation",
        "color": "#facc15", "angular_speed": 0.9,
    },
    "GEO": {
        "radius": 2.8, "altitude": "35,786 km", "speed": "3.07 km/s",
        "speed_kms": 3.07, "period": "24 Hours", "mission": "Communication",
        "color": "#a78bfa", "angular_speed": 0.45,
    },
}

# Pull out the focused satellite's params for the sidebar metrics / info boxes.
radius = ORBITS[orbit_type]["radius"]
altitude = ORBITS[orbit_type]["altitude"]
speed = ORBITS[orbit_type]["speed"]
speed_kms = ORBITS[orbit_type]["speed_kms"]
period = ORBITS[orbit_type]["period"]
mission = ORBITS[orbit_type]["mission"]


# ---------------------------------
# Per-orbit angles & trails (persist across autorefresh reruns)
# ---------------------------------

TRAIL_LENGTH = 25

if "angles" not in st.session_state:
    st.session_state.angles = {"LEO": 0.0, "MEO": 60.0, "GEO": 200.0}  # staggered start

if "trails" not in st.session_state:
    st.session_state.trails = {
        name: deque(maxlen=TRAIL_LENGTH) for name in ORBITS
    }

# Advance every satellite's angle each tick and record its trail point.
for name, params in ORBITS.items():
    st.session_state.angles[name] = (st.session_state.angles[name] + params["angular_speed"]) % 360
    theta = np.deg2rad(st.session_state.angles[name])
    x = params["radius"] * np.cos(theta)
    y = params["radius"] * np.sin(theta)
    st.session_state.trails[name].append((x, y))

angle = st.session_state.angles[orbit_type]  # focused satellite's angle, used below


# ---------------------------------
# Simulated Ground Track (Latitude / Longitude) — for the focused satellite
# ---------------------------------

ORBIT_INCLINATION = 51.6  # degrees, similar to the ISS's real inclination

latitude = ORBIT_INCLINATION * np.sin(np.deg2rad(angle))
longitude = ((angle * 2 + 180) % 360) - 180  # sweeps across -180..180


# ---------------------------------
# Live Telemetry Simulation (ALL satellites, every tick)
# ---------------------------------
# Previously this only ran for the focused satellite. Now every satellite
# gets its own day/night + ground-station-range check (based on its own
# angle) and its own history, so the Fleet Overview panel below always has
# fresh numbers for all three, no matter which one is focused.

SUN_DIRECTION = 0            # must match utils/drawing.py
GROUND_STATION_ANGLE = -60   # must match utils/drawing.py

sun_unit = np.array([np.cos(np.deg2rad(SUN_DIRECTION)), np.sin(np.deg2rad(SUN_DIRECTION))])
gs_unit = np.array([np.cos(np.deg2rad(GROUND_STATION_ANGLE)), np.sin(np.deg2rad(GROUND_STATION_ANGLE))])

TELEMETRY_LENGTH = 40

# Telemetry history is kept per orbit type, so switching the dropdown
# shows that satellite's own history instead of mixing them together.
if "telemetry" not in st.session_state:
    st.session_state.telemetry = {
        name: {
            "battery_hist": deque(maxlen=TELEMETRY_LENGTH),
            "temp_hist": deque(maxlen=TELEMETRY_LENGTH),
            "signal_hist": deque(maxlen=TELEMETRY_LENGTH),
            "speed_hist": deque(maxlen=TELEMETRY_LENGTH),
        }
        for name in ORBITS
    }

for name, params in ORBITS.items():
    sat_theta = np.deg2rad(st.session_state.angles[name])
    sat_unit = np.array([np.cos(sat_theta), np.sin(sat_theta)])

    sat_in_daylight = np.dot(sat_unit, sun_unit) > 0
    sat_in_range = np.dot(sat_unit, gs_unit) > 0

    sat_hist = st.session_state.telemetry[name]

    # --- Battery: charges in daylight, drains in shadow ---
    last_battery = sat_hist["battery_hist"][-1] if sat_hist["battery_hist"] else 95.0
    sat_battery = last_battery + (0.3 if sat_in_daylight else -0.15) + np.random.uniform(-0.1, 0.1)
    sat_battery = float(np.clip(sat_battery, 20, 100))
    sat_hist["battery_hist"].append(sat_battery)

    # --- Temperature: warmer in daylight, colder in shadow ---
    sat_target_temp = 35 if sat_in_daylight else -5
    last_temp = sat_hist["temp_hist"][-1] if sat_hist["temp_hist"] else 28.0
    sat_temp = last_temp + (sat_target_temp - last_temp) * 0.15 + np.random.uniform(-0.5, 0.5)
    sat_hist["temp_hist"].append(sat_temp)

    # --- Signal: strong near ground station, weak far away ---
    sat_target_signal = 95 if sat_in_range else 25
    last_signal = sat_hist["signal_hist"][-1] if sat_hist["signal_hist"] else 90.0
    sat_signal = last_signal + (sat_target_signal - last_signal) * 0.25 + np.random.uniform(-2, 2)
    sat_signal = float(np.clip(sat_signal, 0, 100))
    sat_hist["signal_hist"].append(sat_signal)

    # --- Speed: real orbital speed plus small realistic jitter ---
    sat_current_speed = params["speed_kms"] + np.random.uniform(-0.05, 0.05)
    sat_hist["speed_hist"].append(sat_current_speed)

# Convenience references for the focused satellite, used by the existing
# metrics/charts UI below (keeps the rest of the file unchanged).
hist = st.session_state.telemetry[orbit_type]
battery = hist["battery_hist"][-1]
temperature = hist["temp_hist"][-1]
signal = hist["signal_hist"][-1]


# ---------------------------------
# Main Visualization
# ---------------------------------

left, right = st.columns([2, 1])


with left:

    st.subheader("🌍 Live Satellite Orbit View")

    satellites = []
    for name, params in ORBITS.items():
        satellites.append({
            "label": name,
            "angle": st.session_state.angles[name],
            "radius": params["radius"],
            "color": params["color"],
            "trail": list(st.session_state.trails[name])[:-1],  # exclude current point
            "focused": name == orbit_type,
        })

    fig = draw_earth_and_orbit(
        satellites=satellites,
        moon_angle=moon_angle
    )

    st.pyplot(fig)
    plt.close(fig)


with right:

    st.subheader(f"🛰 {orbit_type} Status")

    st.metric("Battery", f"{battery:.0f}%")
    st.progress(int(battery))

    st.metric("Signal", f"{signal:.0f}%")

    st.metric("Temperature", f"{temperature:.0f}°C")

    st.metric("Velocity", speed)

    st.metric("Altitude", altitude)

    st.metric("Current Angle", f"{int(angle)}°")

    st.metric("Latitude", f"{latitude:.2f}°")
    st.metric("Longitude", f"{longitude:.2f}°")

    st.success("🟢 Satellite Operating Normally")


# ---------------------------------
# Fleet Overview (all 3 satellites at a glance)
# ---------------------------------

st.markdown("---")

st.subheader("🛰️ Fleet Overview")

fleet_cols = st.columns(3)

for col, name in zip(fleet_cols, ORBITS.keys()):
    fleet_hist = st.session_state.telemetry[name]
    fb = fleet_hist["battery_hist"][-1]
    fs = fleet_hist["signal_hist"][-1]
    ft = fleet_hist["temp_hist"][-1]
    color = ORBITS[name]["color"]

    with col:
        label = f"⭐ {name}" if name == orbit_type else name
        st.markdown(f"<span style='color:{color}; font-weight:bold;'>{label}</span>", unsafe_allow_html=True)
        st.progress(int(fb))
        st.caption(f"🔋 {fb:.0f}%   📡 {fs:.0f}%   🌡️ {ft:.0f}°C")


# ---------------------------------
# Live Telemetry Charts (for the focused satellite)
# ---------------------------------

st.markdown("---")

st.subheader(f"📊 Live Telemetry — {orbit_type}")

chart_col1, chart_col2 = st.columns(2)
chart_col3, chart_col4 = st.columns(2)

with chart_col1:
    st.caption("Battery (%)")
    battery_df = pd.DataFrame({"Battery": list(hist["battery_hist"])})
    st.line_chart(battery_df, height=180)

with chart_col2:
    st.caption("Temperature (°C)")
    temp_df = pd.DataFrame({"Temperature": list(hist["temp_hist"])})
    st.line_chart(temp_df, height=180)

with chart_col3:
    st.caption("Signal Strength (%)")
    signal_df = pd.DataFrame({"Signal": list(hist["signal_hist"])})
    st.line_chart(signal_df, height=180)

with chart_col4:
    st.caption("Speed (km/s)")
    speed_df = pd.DataFrame({"Speed": list(hist["speed_hist"])})
    st.line_chart(speed_df, height=180)


# ---------------------------------
# Satellite Information
# ---------------------------------

st.markdown("---")

st.subheader("📡 Orbit Information")


col1, col2, col3 = st.columns(3)

with col1:
    st.info(f"""
**Orbit Type**

{orbit_type}
""")

with col2:
    st.info(f"""
**Altitude**

{altitude}
""")

with col3:
    st.info(f"""
**Velocity**

{speed}
""")


col4, col5, col6 = st.columns(3)

with col4:
    st.info(f"""
**Orbital Period**

{period}
""")

with col5:
    st.info(f"""
**Satellite Angle**

{int(angle)}°
""")

with col6:
    st.info(f"""
**Mission**

{mission}
""")


# ---------------------------------
# Footer
# ---------------------------------

st.markdown("---")

st.markdown(
    """
<center>
🚀 OrbitVision | Space Technology Simulation Platform
</center>
""",
    unsafe_allow_html=True
)