import mysql.connector as db
import requests
import math
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from datetime import datetime, timedelta
import numpy as np

# API keys
AERODATABOX_KEY = "cc6c5307bfmshc5fcc44eee96f40p1356d4jsn4591ecfadea2"
OWM_KEY = "db708f843c1310d2a6fab3b445758485"

# Headers for AeroDataBox API
HEADERS = {
    "X-RapidAPI-Key": AERODATABOX_KEY,
    "X-RapidAPI-Host": "aerodatabox.p.rapidapi.com"
}

# Utility Functions
def get_airport_coords(icao):   
    """Fetch airport lat/lon from AeroDataBox API."""
    url = f"https://aerodatabox.p.rapidapi.com/airports/icao/{icao}"
    try:
        r = requests.get(url, headers=HEADERS)
        r.raise_for_status()
        data = r.json()
        if 'location' in data and 'lat' in data['location'] and 'lon' in data['location']:
            return float(data['location']['lat']), float(data['location']['lon'])
        else:
            raise ValueError(f"No location data found for ICAO code {icao}")
    except requests.RequestException as e:
        print(f"Error fetching airport coords for {icao}: {e}")
        raise

def haversine_distance(lat1, lon1, lat2, lon2):
    """Great-circle distance in nautical miles."""
    R = 6371  # km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * \
        math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return (R*c) * 0.539957  # km to NM

def calculate_bearing(lat1, lon1, lat2, lon2):
    """Initial heading in degrees."""
    dlon = math.radians(lon2 - lon1)
    lat1_rad, lat2_rad = math.radians(lat1), math.radians(lat2)
    y = math.sin(dlon) * math.cos(lat2_rad)
    x = math.cos(lat1_rad) * math.sin(lat2_rad) - \
        math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon)
    return (math.degrees(math.atan2(y, x)) + 360) % 360

def midpoint_coords(lat1, lon1, lat2, lon2):
    """Calculate midpoint lat/lon on great circle."""
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    bx = math.cos(lat2_rad) * math.cos(lon2_rad - lon1_rad)
    by = math.cos(lat2_rad) * math.sin(lon2_rad - lon1_rad)
    mid_lat = math.degrees(math.atan2(math.sin(lat1_rad) + math.sin(lat2_rad), math.sqrt((math.cos(lat1_rad) + bx)**2 + by**2)))
    mid_lon = math.degrees(lon1_rad + math.atan2(by, math.cos(lat1_rad) + bx))
    return mid_lat, mid_lon

def get_wind_data(lat, lon):
    """Wind speed (kts) and direction from OpenWeather."""
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"lat": lat, "lon": lon, "appid": OWM_KEY, "units": "metric"}
    r = requests.get(url, params=params)
    r.raise_for_status()
    data = r.json()
    wind_speed_ms = data['wind']['speed']
    wind_deg = data['wind'].get('deg', 0)
    return wind_speed_ms * 1.94384, wind_deg  # m/s to kts

def flight_traffic_on_route(origin_icao, dest_icao, custom_time=None):
    """Count flights between airports at a specified time."""
    if custom_time is None:
        custom_time = datetime.utcnow()
    else:
        if isinstance(custom_time, str):
            try:
                custom_time = datetime.strptime(custom_time, '%Y-%m-%d %H:%M')
            except ValueError:
                print(f"Invalid time format. Expected 'YYYY-MM-DD HH:MM', got '{custom_time}'")
                return 0  

    from_time = (custom_time - timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M')
    to_time = (custom_time + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M')
    
    url = f"https://aerodatabox.p.rapidapi.com/flights/airports/icao/{origin_icao}/{from_time}/{to_time}"
    querystring = {"direction": "Departure", "destinationIcao": dest_icao}
    try:
        r = requests.get(url, headers=HEADERS, params=querystring)
        r.raise_for_status()
        data = r.json()
        return len(data.get('departures', []))
    except requests.RequestException:
        print("Error fetching flight traffic data")
        return 0

# Core Optimization
def optimize_flight_path(origin_icao, dest_icao, custom_time=None, passng=150):
    con = db.connect(host='localhost', user='root', passwd='mysql', database='flights')
    cur = con.cursor()
    
    lat1, lon1 = get_airport_coords(origin_icao)
    lat2, lon2 = get_airport_coords(dest_icao)
    distance_nm = haversine_distance(lat1, lon1, lat2, lon2)
    heading = calculate_bearing(lat1, lon1, lat2, lon2)
    
    mid_lat, mid_lon = midpoint_coords(lat1, lon1, lat2, lon2)
    wind_speed_kts, wind_dir_deg = get_wind_data(mid_lat, mid_lon)
    angle_diff = math.radians(wind_dir_deg - heading)
    tailwind_component = wind_speed_kts * math.cos(angle_diff)
    
    q = 'select type, airspeed_kts, fuel_rate_kg_h, passengers FROM airplanes'
    cur.execute(q)
    a = cur.fetchall()

    planes = [i for i in a if i[3] >= passng]
    
    min_fuel, min_time = float('inf'), float('inf')
    best_fuel_plane, best_time_plane = None, None
    
    for plane_type, airspeed_kts, fuel_rate_kg_h, passengers in planes:
        gs = airspeed_kts + tailwind_component 
        if gs <= 0:   
            continue
        time_hr = distance_nm / gs    
        fuel_used = fuel_rate_kg_h * time_hr   

        if fuel_used < min_fuel:
            min_fuel = fuel_used
            best_fuel_plane = plane_type
        if time_hr < min_time:
            min_time = time_hr
            best_time_plane = plane_type
    
    flights_active = flight_traffic_on_route(origin_icao, dest_icao, custom_time)
    con.close()

    return {
        "origin": origin_icao,
        "dest": dest_icao,
        "best_airplane_fuel": best_fuel_plane,
        "min_fuel_kg": round(min_fuel, 2) if min_fuel != float('inf') else 0,
        "best_airplane_time": best_time_plane,
        "min_time_hours": round(min_time, 2) if min_time != float('inf') else 0,
        "distance_nm": round(distance_nm, 2),
        "tailwind_kts": round(tailwind_component, 2),
        "flights_in_air": flights_active,
        "coords": ((lat1, lon1), (lat2, lon2)),
        "passengers": passng
    }

def optimize_with_connection(origin, dest, hubs, custom_time=None, passng=150):
    best_option = ("direct", optimize_flight_path(origin, dest, custom_time, passng), None)
    for hub in hubs:
        if hub in (origin, dest):
            continue
        leg1 = optimize_flight_path(origin, hub, custom_time, passng)
        leg2 = optimize_flight_path(hub, dest, custom_time, passng)
        total_fuel = leg1["min_fuel_kg"] + leg2["min_fuel_kg"]
        total_time = leg1["min_time_hours"] + leg2["min_time_hours"] + 1  

        if total_fuel < best_option[1]["min_fuel_kg"]:
            best_option = ("connection", leg1, leg2)
        if total_time < best_option[1]["min_time_hours"]:
            best_option = ("connection", leg1, leg2)

    return best_option

# ─────────────────────────────────────────────────────────────────────────────
#  Plot ROutes  →  
# ─────────────────────────────────────────────────────────────────────────────
def plot_route(routes):
    """
    Plot flight routes with TRUE great-circle curves.
    Flight + Airplane label is cleanly placed BELOW the arc.
    """
    import cartopy.feature as cfeature
    import cartopy.crs as ccrs
    import matplotlib.pyplot as plt
    import numpy as np

    # ============================================================
    # 1. Setup – Dark mode, PlateCarree
    # ============================================================
    plt.style.use('dark_background')
    fig = plt.figure(figsize=(18, 10), dpi=150)
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.set_global()
    ax.patch.set_facecolor('#0a0e17')

    # ============================================================
    # 2. Base map – always show water & land
    # ============================================================
    ax.add_feature(cfeature.OCEAN,   facecolor='#0f1b2e', zorder=0)
    ax.add_feature(cfeature.LAND,    facecolor='#1a2a1f', zorder=0)
    ax.add_feature(cfeature.COASTLINE, edgecolor='#88c0d0', linewidth=0.7, zorder=3)
    ax.add_feature(cfeature.LAKES,     facecolor='#0f2b4e', edgecolor='#88c0d0', linewidth=0.5, zorder=3)
    ax.add_feature(cfeature.RIVERS,    edgecolor='#5e81ac', linewidth=0.4, zorder=3)

    countries = cfeature.NaturalEarthFeature(
        'cultural', 'admin_0_countries', '50m',
        facecolor='none', edgecolor='#4c566a', linewidth=0.5)
    ax.add_feature(countries, zorder=2)

    # ============================================================
    # 3. Helper: Midpoint on great-circle (for label)
    # ============================================================
    def great_circle_midpoint(lon1, lat1, lon2, lat2):
        geod = ccrs.Geodetic()
        mid = geod.transform_point(
            (lon1 + lon2) / 2, (lat1 + lat2) / 2, ccrs.PlateCarree())
        return mid[1], mid[0]  # (lat, lon) in map coords

    # ============================================================
    # 4. Plot routes – TRUE CURVED PATH
    # ============================================================
    first = True
    for route in routes:
        (lat1, lon1), (lat2, lon2) = route["coords"]
        origin = route.get("origin_icao", "ORIG")
        dest = route.get("destination_icao", "DEST")
        flight = route.get("flight_number", "FLIGHT")
        airplane = route.get("best_airplane_fuel", "A320").split("_")[0]

        # --- CURVED GREAT-CIRCLE PATH ---
        ax.plot([lon1, lon2], [lat1, lat2],
                color='#00ffcc', linewidth=3, alpha=0.95,
                transform=ccrs.Geodetic(),  # ← REAL CURVE
                label='Flight Route' if first else None, zorder=5)

        # Glow
        ax.plot([lon1, lon2], [lat1, lat2],
                color='#00aaff', linewidth=6, alpha=0.35,
                transform=ccrs.Geodetic(), zorder=4)
        first = False

        # --- Origin / Destination ---
        ax.plot(lon1, lat1, 'o', color='#00ccff', markersize=11,
                transform=ccrs.PlateCarree(), markeredgecolor='white',
                markeredgewidth=1.5, zorder=10)
        ax.plot(lon2, lat2, 'o', color='#ff3366', markersize=11,
                transform=ccrs.PlateCarree(), markeredgecolor='white',
                markeredgewidth=1.5, zorder=10)

        # --- ICAO Labels (offset) ---
        ax.text(lon1 + 2, lat1 + 2, origin,
                fontsize=11, color='#00ccff', fontweight='bold',
                transform=ccrs.PlateCarree(),
                bbox=dict(facecolor='#0a0e17', edgecolor='#00ccff', linewidth=1.2, pad=3, alpha=0.9),
                zorder=11)

        ax.text(lon2 + 2, lat2 + 2, dest,
                fontsize=11, color='#ff3366', fontweight='bold',
                transform=ccrs.PlateCarree(),
                bbox=dict(facecolor='#0a0e17', edgecolor='#ff3366', linewidth=1.2, pad=3, alpha=0.9),
                zorder=11)

        # --- FLIGHT + AIRPLANE LABEL: MOVED BELOW THE CURVE ---
        mid_lat, mid_lon = great_circle_midpoint(lon1, lat1, lon2, lat2)
        label = f"{airplane} – {flight}"

        # Push label DOWN by 8° latitude for clean placement
        label_lat = mid_lat - 8
        ax.text(mid_lon, label_lat, label,
                fontsize=12, color='white', fontweight='bold',
                transform=ccrs.PlateCarree(), ha='center', va='top',
                bbox=dict(facecolor='#ff9500', edgecolor='none', alpha=0.9, pad=4),
                zorder=12)

    # ============================================================
    # 5. Gridlines
    # ============================================================
    gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True,
                      linewidth=0.6, color='#4c566a', alpha=0.7, linestyle='--')
    gl.top_labels = gl.right_labels = False
    gl.xformatter = ccrs.cartopy.mpl.gridliner.LongitudeFormatter()
    gl.yformatter = ccrs.cartopy.mpl.gridliner.LatitudeFormatter()
    gl.xlabel_style = {'size': 9, 'color': '#d8dee9'}
    gl.ylabel_style = {'size': 9, 'color': '#d8dee9'}

    # ============================================================
    # 6. Scale bar
    # ============================================================
    km_per_degree = 111
    scale_km = 2000
    scale_deg = scale_km / km_per_degree
    x0, y0 = -170, -55
    x1 = x0 + scale_deg

    ax.plot([x0, x1], [y0, y0], color='white', linewidth=4, transform=ccrs.PlateCarree())
    ax.plot([x0, x0], [y0-1, y0+1], color='white', linewidth=4, transform=ccrs.PlateCarree())
    ax.plot([x1, x1], [y0-1, y0+1], color='white', linewidth=4, transform=ccrs.PlateCarree())
    ax.text((x0+x1)/2, y0+3, f"{scale_km} km", color='white', fontsize=10,
            fontweight='bold', ha='center', transform=ccrs.PlateCarree(),
            bbox=dict(facecolor='#0a0e17', edgecolor='none', pad=2, alpha=0.8))

    # ============================================================
    # 7. Title & Legend
    # ============================================================
    plt.title("Global Flight Routes – Optimized Paths",
              fontsize=20, color='white', pad=30, fontweight='bold')

    legend = ax.legend(loc='upper left', frameon=True, fancybox=True,
                       facecolor='#1a2332', edgecolor='#88c0d0',
                       labelcolor='white', fontsize=11)
    legend.get_frame().set_alpha(0.9)

    # ============================================================
    # 8. Save & Show
    # ============================================================
    out_file = "flight_routes_clean_dark.png"
    plt.savefig(out_file, dpi=300, bbox_inches='tight', facecolor='#0a0e17')
    plt.show()
    print(f"Clean map with label below saved: {out_file}")