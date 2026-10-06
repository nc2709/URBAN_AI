import html
import math
import requests
import streamlit as st
import folium
from streamlit_folium import st_folium

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="UrbanMove AI",
    page_icon="🚍",
    layout="wide",
)

# =========================================================
# CONSTANTS
# =========================================================
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OSRM_URL = "https://router.project-osrm.org/route/v1/driving"
REQUEST_HEADERS = {"User-Agent": "UrbanMoveAI/1.0 (route planner demo)"}
TRANSPORT_MODES = ["🚌 Bus", "🚆 Train", "🚇 Metro", "🚗 Car"]

# =========================================================
# SESSION STATE
# =========================================================
if "page" not in st.session_state:
    st.session_state.page = "home"
if "route_result" not in st.session_state:
    st.session_state.route_result = None

# =========================================================
# CSS
# =========================================================
st.markdown(
    """
    <style>
    .stApp { background: linear-gradient(135deg, #eef6ff, #ffffff); }
    h1 { color: #1e3a8a !important; }
    p { color: #334155; }
    .stButton > button {
        background-color: #2563eb;
        color: #000000 !important;
        border: none;
        border-radius: 10px;
        padding: 0.65rem 1rem;
        font-size: 16px;
        font-weight: 600;
    }
    .stButton > button:hover {
        background-color: #1d4ed8;
        color: #000000 !important;
    }
    .stButton > button p { color: #000000 !important; }
    .stTextInput input { border-radius: 8px; }
    [data-testid="stMetric"] {
        background: white;
        border: 1px solid #dbeafe;
        border-radius: 12px;
        padding: 15px;
    }
    .home-space { height: 55px; }
    .home-description, .planner-subtitle {
        text-align: center;
        font-size: 18px;
        color: #64748b !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# GEOCODING
# =========================================================
@st.cache_data(ttl=3600, show_spinner=False)
def geocode(place: str):
    """Find a place using OpenStreetMap's Nominatim service."""
    try:
        response = requests.get(
            NOMINATIM_URL,
            params={"q": place, "format": "jsonv2", "limit": 1},
            headers=REQUEST_HEADERS,
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        if not data:
            return None

        return {
            "lat": float(data[0]["lat"]),
            "lon": float(data[0]["lon"]),
            "name": data[0].get("display_name", place),
        }
    except (requests.RequestException, ValueError, KeyError, IndexError):
        return None


# =========================================================
# ROUTE
# =========================================================
def get_route(start_lat: float, start_lon: float, end_lat: float, end_lon: float):
    """Get a driving route from the public OSRM demo service."""
    url = (
        f"{OSRM_URL}/"
        f"{start_lon},{start_lat};{end_lon},{end_lat}"
    )
    try:
        response = requests.get(
            url,
            params={"overview": "full", "geometries": "geojson"},
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()

        if data.get("code") != "Ok" or not data.get("routes"):
            return None

        route = data["routes"][0]
        return {
            "distance": float(route["distance"]) / 1000.0,
            "duration": float(route["duration"]) / 60.0,
            "geometry": route["geometry"],
        }
    except (requests.RequestException, ValueError, KeyError, IndexError, TypeError):
        return None


# =========================================================
# ESTIMATED FARES
# =========================================================
def calculate_fare(mode: str, distance: float):
    """Demo fare estimates in INR; these are not official fares."""
    if mode == "🚌 Bus":
        if distance <= 5:
            return 10
        if distance <= 10:
            return 15
        if distance <= 15:
            return 20
        if distance <= 25:
            return 25
        return 30

    if mode == "🚆 Train":
        if distance <= 5:
            return 10
        if distance <= 10:
            return 15
        if distance <= 20:
            return 20
        if distance <= 30:
            return 30
        return 40

    if mode == "🚇 Metro":
        if distance <= 5:
            return 15
        if distance <= 10:
            return 25
        if distance <= 15:
            return 30
        if distance <= 20:
            return 40
        if distance <= 30:
            return 50
        return 60

    # Car fare is not estimated because it depends on fuel, tolls,
    # parking, vehicle efficiency, and other factors.
    return None


# =========================================================
# ESTIMATED TRAVEL TIME
# =========================================================
def estimate_time(mode: str, road_time: float) -> float:
    """Rough demo estimate based on driving time, not live transit data."""
    if mode == "🚗 Car":
        return road_time
    if mode == "🚌 Bus":
        return road_time * 1.35 + 8
    if mode == "🚆 Train":
        return road_time * 1.15 + 10
    if mode == "🚇 Metro":
        return road_time * 0.85 + 8
    return road_time


def format_time(minutes: float) -> str:
    minutes = max(0, int(round(minutes)))
    if minutes < 60:
        return f"{minutes} min"
    hours, mins = divmod(minutes, 60)
    return f"{hours} hr" if mins == 0 else f"{hours} hr {mins} min"


# =========================================================
# HOME PAGE
# =========================================================
if st.session_state.page == "home":
    st.markdown("<div class='home-space'></div>", unsafe_allow_html=True)
    st.markdown(
        "<h1 style='text-align:center; font-size:60px;'>🚍</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<h1 style='text-align:center;'>UrbanMove AI</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <h3 style='text-align:center; color:#475569;'>
        Intelligent Urban Route &amp; Fare Planner
        </h3>
        <p class="home-description">
        Plan a journey with location search, route mapping, distance calculation,
        estimated travel time and estimated transport fares.
        </p>
        """,
        unsafe_allow_html=True,
    )
    st.write("")
    _, center_col, _ = st.columns([1, 1, 1])
    with center_col:
        if st.button("🚀 Get Started", use_container_width=True):
            st.session_state.page = "planner"
            st.rerun()

# =========================================================
# PLANNER PAGE
# =========================================================
else:
    if st.button("⬅️ Back to Home"):
        st.session_state.page = "home"
        st.rerun()

    st.title("🚍 UrbanMove AI")
    st.markdown(
        "<p class='planner-subtitle'>Intelligent Urban Route &amp; Fare Planner</p>",
        unsafe_allow_html=True,
    )
    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        start = st.text_input(
            "📍 Starting Location",
            placeholder="Example: Secunderabad, Hyderabad",
            key="start_location_input",
        )
    with col2:
        destination = st.text_input(
            "🏁 Destination",
            placeholder="Example: Charminar, Hyderabad",
            key="destination_input",
        )

    mode = st.selectbox("🚘 Select Transport", TRANSPORT_MODES)
    st.caption(
        "Note: this demo uses a driving route as the distance baseline. "
        "Public transport routes, schedules and official fares are not live."
    )

    if st.button("🔎 Find Route", use_container_width=True):
        st.session_state.route_result = None

        if not start.strip():
            st.error("Please enter the starting location.")
        elif not destination.strip():
            st.error("Please enter the destination.")
        else:
            with st.spinner("🌍 Finding locations and calculating route..."):
                start_location = geocode(start.strip())
                end_location = geocode(destination.strip())

            if start_location is None:
                st.error(
                    f"Could not find '{start}'. Try adding the city or region."
                )
            elif end_location is None:
                st.error(
                    f"Could not find '{destination}'. Try adding the city or region."
                )
            elif (
                math.isclose(start_location["lat"], end_location["lat"], abs_tol=1e-6)
                and math.isclose(start_location["lon"], end_location["lon"], abs_tol=1e-6)
            ):
                st.error("The starting location and destination appear to be the same.")
            else:
                with st.spinner("🛣️ Calculating route..."):
                    route = get_route(
                        start_location["lat"],
                        start_location["lon"],
                        end_location["lat"],
                        end_location["lon"],
                    )

                if route is None:
                    st.error(
                        "Could not calculate a route. Please try again later or "
                        "check whether the locations are reachable by road."
                    )
                else:
                    distance = route["distance"]
                    road_time = route["duration"]
                    travel_time = estimate_time(mode, road_time)
                    fare = calculate_fare(mode, distance)

                    st.session_state.route_result = {
                        "start": start.strip(),
                        "destination": destination.strip(),
                        "mode": mode,
                        "start_location": start_location,
                        "end_location": end_location,
                        "route": route,
                        "distance": distance,
                        "travel_time": travel_time,
                        "fare": fare,
                    }

    # Render the saved result on every rerun, not only on the button click.
    result = st.session_state.route_result
    if result:
        st.success("✅ Route found successfully!")

        distance = result["distance"]
        travel_time = result["travel_time"]
        fare = result["fare"]
        start_location = result["start_location"]
        end_location = result["end_location"]
        route = result["route"]

        col1, col2, col3 = st.columns(3)
        col1.metric("📏 Distance", f"{distance:.2f} km")
        col2.metric("⏱️ Estimated Travel Time", format_time(travel_time))
        col3.metric(
            "💰 Estimated Fare",
            f"₹{fare}" if fare is not None else "N/A",
        )

        st.subheader("📌 Journey Details")
        st.write(f"**Starting Location:** {start_location['name']}")
        st.write(f"**Destination:** {end_location['name']}")
        st.write(f"**Transport:** {result['mode']}")
        st.write(f"**Route distance (driving):** {distance:.2f} km")
        st.write(f"**Estimated travel time:** {format_time(travel_time)}")
        if fare is not None:
            st.write(f"**Estimated fare:** ₹{fare}")
        else:
            st.write(
                "**Car cost:** Not calculated. Actual cost depends on fuel, "
                "vehicle efficiency, tolls and parking."
            )

        st.info(
            "This is a student/demo estimate. The route distance comes from "
            "OSRM/OpenStreetMap driving directions. Bus, train and metro times "
            "and fares are approximate estimates and may differ from real services."
        )

        st.subheader("🗺️ Route Map")
        center_lat = (start_location["lat"] + end_location["lat"]) / 2
        center_lon = (start_location["lon"] + end_location["lon"]) / 2
        route_map = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=12,
            control_scale=True,
        )

        folium.Marker(
            [start_location["lat"], start_location["lon"]],
            popup=f"Start: {html.escape(result['start'])}",
            tooltip="Starting Location",
            icon=folium.Icon(color="green", icon="play"),
        ).add_to(route_map)

        folium.Marker(
            [end_location["lat"], end_location["lon"]],
            popup=f"Destination: {html.escape(result['destination'])}",
            tooltip="Destination",
            icon=folium.Icon(color="red", icon="flag"),
        ).add_to(route_map)

        coordinates = [
            [point[1], point[0]]
            for point in route["geometry"].get("coordinates", [])
        ]
        if coordinates:
            folium.PolyLine(
                coordinates,
                color="#2563eb",
                weight=6,
                opacity=0.85,
                tooltip="Calculated driving route",
            ).add_to(route_map)

        route_map.fit_bounds(
            [
                [start_location["lat"], start_location["lon"]],
                [end_location["lat"], end_location["lon"]],
            ],
            padding=(25, 25),
        )
        st_folium(route_map, use_container_width=True, height=550)
