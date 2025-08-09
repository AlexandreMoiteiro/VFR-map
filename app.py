
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster
from pathlib import Path
import re
import json

st.set_page_config(page_title="Portugal VFR — Localidades + AD/HEL/ULM", layout="wide")

# --------- Helpers ---------
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
    return pd.DataFrame(rows).dropna(subset=["lat","lon"])

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
    return pd.DataFrame(rows).dropna(subset=["lat","lon"])

# --------- Load bundled data (no sidebar, no uploads) ---------
ad = pd.read_csv("AD-HEL-ULM.csv")
loc = pd.read_csv("Localidades-Nova-versao-230223.csv")
ad_df = parse_ad(ad)
loc_df = parse_localidades(loc)

# --------- Top controls (minimal) ---------
col1, col2, col3, col4 = st.columns([1,1,1,4])
with col1:
    show_ad = st.checkbox("Aeródromos", value=True)
with col2:
    show_loc = st.checkbox("Localidades", value=True)
with col3:
    show_sectors = st.checkbox("Áreas dos sectores", value=False)
with col4:
    query = st.text_input("Filtrar (código/ident/nome/cidade/sector)", "", placeholder="Ex.: TMA-PRT, ABRAN, LP0078...")

def apply_filters(ad_df, loc_df):
    ad_out = ad_df.copy()
    loc_out = loc_df.copy()
    if query:
        q = query.lower().strip()
        ad_out = ad_out[ad_out.apply(lambda r: q in str(r["name"]).lower() or q in str(r.get("ident","")).lower() or q in str(r.get("city","")).lower(), axis=1)]
        loc_out = loc_out[loc_out.apply(lambda r: q in str(r["name"]).lower() or q in str(r.get("code","")).lower() or q in str(r.get("sector","")).lower(), axis=1)]
    return ad_out, loc_out

ad_f, loc_f = apply_filters(ad_df, loc_df)

# Map center
if len(ad_f) + len(loc_f) > 0:
    mean_lat = pd.concat([ad_f["lat"], loc_f["lat"]]).mean()
    mean_lon = pd.concat([ad_f["lon"], loc_f["lon"]]).mean()
else:
    mean_lat, mean_lon = 39.5, -8.0

# --------- Base map (Carto Positron, no API key) ---------
m = folium.Map(location=[mean_lat, mean_lon], zoom_start=6, tiles="CartoDB Positron", control_scale=True)

# A: Localidades — show 5-letter code as label, tooltip shows name + sector
if show_loc and not loc_f.empty:
    cluster_loc = MarkerCluster(name="Localidades", show=True, disableClusteringAtZoom=10)
    for _, r in loc_f.iterrows():
        code = r.get("code") or ""
        tooltip_html = "<b>{}</b><br/>Sector: {}<br/>Código: {}".format(r.get('name',''), r.get('sector',''), code)
        # Small pill label with the 5-letter code
        label_html = (
            '<div style="font-size:11px;font-weight:600;color:#1e3a8a;'
            'background:rgba(255,255,255,0.9);padding:2px 4px;border-radius:4px;'
            'border:1px solid #cbd5e1;">{}</div>'.format(code)
        )
        folium.Marker(
            location=[r["lat"], r["lon"]],
            icon=folium.DivIcon(html=label_html),
            tooltip=tooltip_html
        ).add_to(cluster_loc)
    cluster_loc.add_to(m)

# B: AD/HEL/ULM — different icon (airfield), tooltip with name/city/ident
if show_ad and not ad_f.empty:
    cluster_ad = MarkerCluster(name="AD/HEL/ULM", show=True, disableClusteringAtZoom=10)
    for _, r in ad_f.iterrows():
        tooltip_html = "<b>{}</b><br/>Ident: {}<br/>Cidade: {}".format(r.get('name',''), r.get('ident',''), r.get('city',''))
        folium.Marker(
            location=[r["lat"], r["lon"]],
            icon=folium.Icon(icon="plane", prefix="fa"),
            tooltip=tooltip_html
        ).add_to(cluster_ad)
    cluster_ad.add_to(m)

# C: Sector polygons (optional). If sectors.geojson is present, add it and allow toggle.
# The file should be a FeatureCollection with properties 'name' or 'sector' to show.
if show_sectors:
    try:
        with open("sectors.geojson", "r", encoding="utf-8") as f:
            gj = json.load(f)
        folium.GeoJson(
            gj,
            name="Áreas dos sectores",
            tooltip=folium.GeoJsonTooltip(fields=["name","sector"], aliases=["Nome","Sector"], sticky=True),
            style_function=lambda feat: {"fillColor": "#3b82f6", "color": "#1d4ed8", "weight": 1, "fillOpacity": 0.15}
        ).add_to(m)
    except Exception:
        st.info("Para ver as áreas dos sectores, coloque um ficheiro **sectors.geojson** na mesma pasta do app (GeoJSON WGS84).")

folium.LayerControl(collapsed=True).add_to(m)

st_folium(m, width=None, height=680)
st.caption(f"Carregados {len(ad_df)} AD/HEL/ULM e {len(loc_df)} Localidades. Filtro → AD: {len(ad_f)} | Localidades: {len(loc_f)}.")
