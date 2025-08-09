
import streamlit as st
import pandas as pd
import pydeck as pdk
import re
from pathlib import Path

st.set_page_config(page_title="Portugal — AD/HEL/ULM + Localidades Map", layout="wide")

st.title("🗺️ Portugal: AD/HEL/ULM + Localidades")
st.caption("Loads the provided CSVs, parses DMS coordinates, and plots everything on a single interactive map.")

DATA_DIR = Path(".")

# --- Helpers ---
@st.cache_data(show_spinner=False)
def load_csvs(ad_path: str, loc_path: str):
    ad = pd.read_csv(ad_path)
    loc = pd.read_csv(loc_path)
    return ad, loc

def dms_to_dd(token: str, is_lon=False):
    token = str(token).strip()
    m = re.match(r"^(\d+(?:\.\d+)?)([NSEW])$", token, re.I)
    if not m:
        return None
    value, hemi = m.groups()
    if "." in value:
        if is_lon:
            deg = int(value[0:3])
            minutes = int(value[3:5])
            seconds = float(value[5:])
        else:
            deg = int(value[0:2])
            minutes = int(value[2:4])
            seconds = float(value[4:])
    else:
        if is_lon:
            deg = int(value[0:3])
            minutes = int(value[3:5])
            seconds = int(value[5:])
        else:
            deg = int(value[0:2])
            minutes = int(value[2:4])
            seconds = int(value[4:])
    dd = deg + minutes/60 + seconds/3600
    if hemi.upper() in ["S","W"]:
        dd = -dd
    return dd

def parse_ad(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for line in df.iloc[:,0].dropna().tolist():
        s = str(line).strip()
        if not s or s.startswith(("Ident", "DEP/")):
            continue
        tokens = s.split()
        coord_toks = [t for t in tokens if re.match(r"^\d+(?:\.\d+)?[NSEW]$", t)]
        if len(coord_toks) >= 2:
            lat_tok = coord_toks[-2]
            lon_tok = coord_toks[-1]
            lat = dms_to_dd(lat_tok, is_lon=False)
            lon = dms_to_dd(lon_tok, is_lon=True)
            ident = tokens[0] if re.match(r"^[A-Z0-9]{4,}$", tokens[0]) else None
            try:
                name = " ".join(tokens[1:tokens.index(coord_toks[0])]).strip()
            except ValueError:
                name = " ".join(tokens[1:]).strip()
            try:
                lon_idx = tokens.index(lon_tok)
                city = " ".join(tokens[lon_idx+1:]) or None
            except ValueError:
                city = None
            rows.append({"source":"AD/HEL/ULM","ident":ident,"name":name,"city":city,"lat":lat,"lon":lon})
    out = pd.DataFrame(rows).dropna(subset=["lat","lon"])
    return out

def parse_localidades(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for line in df.iloc[:,0].dropna().tolist():
        s = str(line).strip()
        if not s or "Total de registos" in s:
            continue
        tokens = s.split()
        coord_toks = [t for t in tokens if re.match(r"^\d{6,7}(?:\.\d+)?[NSEW]$", t)]
        if len(coord_toks) >= 2:
            lat_tok, lon_tok = coord_toks[0], coord_toks[1]
            lat = dms_to_dd(lat_tok, is_lon=False)
            lon = dms_to_dd(lon_tok, is_lon=True)
            try:
                lon_idx = tokens.index(lon_tok)
            except ValueError:
                continue
            code = tokens[lon_idx+1] if lon_idx+1 < len(tokens) else None
            sector = " ".join(tokens[lon_idx+2:]) if lon_idx+2 < len(tokens) else None
            name = " ".join(tokens[:tokens.index(lat_tok)]).strip()
            rows.append({"source":"Localidade","code":code,"name":name,"sector":sector,"lat":lat,"lon":lon})
    out = pd.DataFrame(rows).dropna(subset=["lat","lon"])
    return out

# --- Sidebar ---
st.sidebar.header("Data sources")
ad_file = st.sidebar.file_uploader("AD-HEL-ULM.csv", type=["csv"], accept_multiple_files=False)
loc_file = st.sidebar.file_uploader("Localidades-Nova-versao-230223.csv", type=["csv"], accept_multiple_files=False)
use_bundled = st.sidebar.checkbox("Use bundled sample files (if no uploads)", value=True)

if ad_file and loc_file:
    ad_raw = pd.read_csv(ad_file)
    loc_raw = pd.read_csv(loc_file)
elif use_bundled:
    # assume files are next to the app
    ad_raw, loc_raw = load_csvs("AD-HEL-ULM.csv", "Localidades-Nova-versao-230223.csv")
else:
    st.info("Upload both CSVs in the sidebar to continue, or tick 'Use bundled sample files'.")
    st.stop()

ad_df = parse_ad(ad_raw)
loc_df = parse_localidades(loc_raw)

st.sidebar.subheader("Filters")
show_ad = st.sidebar.checkbox("Show AD/HEL/ULM", value=True)
show_loc = st.sidebar.checkbox("Show Localidades", value=True)
sector_filter = st.sidebar.multiselect("Localidades — Sector", options=sorted([s for s in loc_df['sector'].dropna().unique().tolist()]), default=[])
text_query = st.sidebar.text_input("Search (name/code/ident/city)", "")

def apply_filters(ad_df, loc_df):
    ad_out = ad_df.copy()
    loc_out = loc_df.copy()
    if text_query:
        tq = text_query.lower()
        ad_out = ad_out[ad_out.apply(lambda r: tq in str(r["name"]).lower() or tq in str(r.get("ident","")).lower() or tq in str(r.get("city","")).lower(), axis=1)]
        loc_out = loc_out[loc_out.apply(lambda r: tq in str(r["name"]).lower() or tq in str(r.get("code","")).lower() or tq in str(r.get("sector","")).lower(), axis=1)]
    if sector_filter:
        loc_out = loc_out[loc_out["sector"].isin(sector_filter)]
    return ad_out, loc_out

ad_f, loc_f = apply_filters(ad_df, loc_df)

# --- Map viewport ---
# Center roughly over Portugal
if len(ad_f) + len(loc_f) > 0:
    mean_lat = pd.concat([ad_f["lat"], loc_f["lat"]]).mean()
    mean_lon = pd.concat([ad_f["lon"], loc_f["lon"]]).mean()
else:
    mean_lat, mean_lon = 39.5, -8.0

view_state = pdk.ViewState(latitude=mean_lat, longitude=mean_lon, zoom=6.2, pitch=0)

layers = []

if show_loc and not loc_f.empty:
    layers.append(
        pdk.Layer(
            "ScatterplotLayer",
            data=loc_f,
            get_position='[lon, lat]',
            get_radius=300,
            radius_min_pixels=2,
            radius_max_pixels=20,
            get_fill_color=[20, 120, 255, 180],
            pickable=True,
        )
    )
    # Optional labels for localidades
    layers.append(
        pdk.Layer(
            "TextLayer",
            data=loc_f,
            get_position='[lon, lat]',
            get_text='name',
            get_size=12,
            get_color=[20, 120, 255, 255],
            get_angle=0,
            get_alignment_baseline="'bottom'",
        )
    )

if show_ad and not ad_f.empty:
    layers.append(
        pdk.Layer(
            "ScatterplotLayer",
            data=ad_f,
            get_position='[lon, lat]',
            get_radius=400,
            radius_min_pixels=3,
            radius_max_pixels=24,
            get_fill_color=[255, 90, 0, 180],
            pickable=True,
        )
    )

tooltip = {
    "html": """
    <b>{source}</b><br/>
    <b>Name:</b> {name}<br/>
    <b>Ident:</b> {ident}<br/>
    <b>City:</b> {city}<br/>
    <b>Code:</b> {code}<br/>
    <b>Sector:</b> {sector}<br/>
    <b>Lat:</b> {lat} <b>Lon:</b> {lon}
    """,
    "style": {"backgroundColor": "rgba(15,15,15,0.9)", "color": "white"}
}

r = pdk.Deck(
    map_style="mapbox://styles/mapbox/light-v11",
    initial_view_state=view_state,
    layers=layers,
    tooltip=tooltip,
)

st.pydeck_chart(r, use_container_width=True)

# --- Data previews
with st.expander("Data samples"):
    st.write("**AD/HEL/ULM**", ad_df.head(20))
    st.write("**Localidades**", loc_df.head(20))

st.success(f"Loaded {len(ad_df)} AD/HEL/ULM points and {len(loc_df)} Localidades. "
           f"Filters -> AD: {len(ad_f)} | Localidades: {len(loc_f)}.")
