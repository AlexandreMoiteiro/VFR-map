# app.py
import re
from pathlib import Path

import pandas as pd
import streamlit as st
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

# ----------------------------
# Configuração da página
# ----------------------------
st.set_page_config(page_title="VFR Map PT", layout="wide")

# Container central (sem sidebar)
st.markdown(
    """
    <style>
      /* esconder sidebar */
      [data-testid="stSidebar"] {display: none;}
      /* centralizar o conteúdo */
      .main > div {display: flex; justify-content: center;}
      .block-container {padding-top: 1rem; max-width: 1200px;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("VFR Map — Portugal (Híbrido)")
st.caption("Localidades + AD / Helis / ULM (dados CSV)")

# ----------------------------
# Caminhos dos ficheiros
# ----------------------------
BASE = Path("/mnt/data")
LOCALIDADES_CSV = BASE / "Localidades-Nova-versao-230223.csv"
AD_CSV = BASE / "AD-HEL-ULM.csv"

# ----------------------------
# Utils
# ----------------------------
def dms_to_decimal(coord: str):
    """
    Converte coordenadas DMS/DM -> decimal.
    Aceita:
      - DDMMSSH / DDDMMSSH            (ex: 404903N, 0091547W)
      - DDMMSS.sH / DDDMMSS.sH       (ex: 372755.90N, 0085613.4W)
      - DDMMH / DDDMMH               (ex: 4049N, 00732W)
    Retorna float (negativo para S/W) ou None.
    """
    if coord is None:
        return None
    s = str(coord).strip().upper().replace(" ", "")
    if not s:
        return None
    # manter apenas dígitos, ponto e N/S/E/W (csvs às vezes trazem lixo)
    s = "".join(ch for ch in s if ch.isdigit() or ch in "NSEW.")
    if not s or s[-1] not in "NSEW":
        return None

    hemi = s[-1]
    body = s[:-1]

    # DMS com segundos (pode ter decimais)
    m = re.match(r"^(\d{2,3})(\d{2})(\d{2}(?:\.\d+)?)$", body)
    if m:
        d, mnt, sec = m.groups()
        val = int(d) + int(mnt) / 60 + float(sec) / 3600
    else:
        # DM sem segundos
        m = re.match(r"^(\d{2,3})(\d{2})$", body)
        if not m:
            return None
        d, mnt = m.groups()
        val = int(d) + int(mnt) / 60

    if hemi in ("S", "W"):
        val = -val
    return val


def split_coord_pair(text: str):
    """
    Extrai (lat, lon) de uma string tipo '392747N 0081159W' (com espaço).
    Retorna (lat_str, lon_str) ou (None, None).
    """
    if not isinstance(text, str):
        return None, None
    s = text.strip().upper()
    parts = re.findall(r"\d+(?:\.\d+)?[NSEW]", s)
    if len(parts) >= 2:
        return parts[0], parts[1]
    return None, None


def build_lat_lon_from_any(df: pd.DataFrame):
    """
    Tenta construir colunas 'lat' e 'lon' a partir de diferentes formatos.
    - Colunas já decimais: LatDecimal / LonDecimal
    - Colunas DMS separadas: Latitude / Longitude (ex: 372755.90N / 0084414.21W)
    - Coluna única: COORDENADAS com '392747N 0081159W'
    - Colunas alternativas vistas nos ficheiros
    """
    # normalizar nomes
    df = df.copy()
    df.columns = [c.strip() for c in df.columns]

    # 1) já decimais?
    lat_col = next((c for c in df.columns if c.lower() in ("latdecimal", "latitude_decimal", "lat_dec")), None)
    lon_col = next((c for c in df.columns if c.lower() in ("londecimal", "longitude_decimal", "lon_dec", "lngdecimal")), None)
    if lat_col and lon_col:
        df["lat"] = pd.to_numeric(df[lat_col], errors="coerce")
        df["lon"] = pd.to_numeric(df[lon_col], errors="coerce")
        return df

    # 2) DMS em colunas 'Latitude' / 'Longitude' (ou variantes)
    lat_cands = [c for c in df.columns if c.lower() in ("latitude", "lat", "lat_dms", "lat dms")]
    lon_cands = [c for c in df.columns if c.lower() in ("longitude", "lon", "lon_dms", "lon dms")]
    if lat_cands and lon_cands:
        lc, lo = lat_cands[0], lon_cands[0]
        df["lat"] = df[lc].apply(dms_to_decimal)
        df["lon"] = df[lo].apply(dms_to_decimal)
        return df

    # 3) coluna única tipo 'COORDENADAS' com "LAT LON"
    single_cands = [c for c in df.columns if c.upper() in ("COORDENADAS", "COORD", "COORDS", "COORD FOR FPL FIELD 18")]
    if single_cands:
        sc = single_cands[0]
        lats, lons = [], []
        for v in df[sc].astype(str).tolist():
            la, lo = split_coord_pair(v)
            lats.append(dms_to_decimal(la) if la else None)
            lons.append(dms_to_decimal(lo) if lo else None)
        df["lat"] = lats
        df["lon"] = lons
        return df

    # 4) tentativa genérica: procurar qualquer par com N/S e E/W
    if "lat" not in df or "lon" not in df:
        # procurar duas colunas que contenham N/S e E/W
        text_cols = [c for c in df.columns if df[c].astype(str).str.contains("[NSEW]", regex=True, na=False).any()]
        if len(text_cols) >= 2:
            # palpite simples: as duas primeiras
            a, b = text_cols[:2]
            # inferir qual é lat (N/S) e qual é lon (E/W)
            sample_a = "".join(re.findall(r"[NSEW]", " ".join(df[a].astype(str).head(50).tolist())))
            sample_b = "".join(re.findall(r"[NSEW]", " ".join(df[b].astype(str).head(50).tolist())))
            lat_col_guess = a if ("N" in sample_a or "S" in sample_a) else b
            lon_col_guess = b if lat_col_guess == a else a
            df["lat"] = df[lat_col_guess].apply(dms_to_decimal)
            df["lon"] = df[lon_col_guess].apply(dms_to_decimal)
            return df

    # se tudo falhar, criar colunas vazias
    df["lat"] = pd.NA
    df["lon"] = pd.NA
    return df


def load_csv_safe(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8", on_bad_lines="skip")


def bounds_from_points(latitudes, longitudes):
    lat_min, lat_max = min(latitudes), max(latitudes)
    lon_min, lon_max = min(longitudes), max(longitudes)
    return [[lat_min, lon_min], [lat_max, lon_max]]


# ----------------------------
# Ler dados
# ----------------------------
try:
    localidades_raw = load_csv_safe(LOCALIDADES_CSV)
except Exception as e:
    st.error(f"Erro a ler {LOCALIDADES_CSV.name}: {e}")
    st.stop()

try:
    ad_raw = load_csv_safe(AD_CSV)
except Exception as e:
    st.error(f"Erro a ler {AD_CSV.name}: {e}")
    st.stop()

localidades = build_lat_lon_from_any(localidades_raw)
ad_df = build_lat_lon_from_any(ad_raw)

# Nome / label (melhor esforço)
def best_name(df):
    for c in ["LOCALIDADE", "Name", "NAME", "Ident", "IDENT", "CÓDIGO 5 LETRAS", "CODIGO 5 LETRAS", "Código 5 Letras"]:
        if c in df.columns:
            return c
    # fallback: primeira coluna de texto
    for c in df.columns:
        if df[c].astype(str).str.len().max() > 0 and c not in ("lat", "lon"):
            return c
    return None

loc_name_col = best_name(localidades) or "LOCALIDADE"
ad_name_col = best_name(ad_df) or "Name"

# Limpar linhas sem coordenadas válidas
localidades = localidades[pd.notna(localidades["lat"]) & pd.notna(localidades["lon"])].copy()
ad_df = ad_df[pd.notna(ad_df["lat"]) & pd.notna(ad_df["lon"])].copy()

if localidades.empty and ad_df.empty:
    st.error("Sem pontos válidos após parsing das coordenadas. Verifica se as colunas contêm DMS (ex: 392747N / 0081159W) ou decimais.")
    st.stop()

# ----------------------------
# Construir o mapa (híbrido)
# ----------------------------
# Mapa vazio (tiles=None), vamos adicionar imagem + labels
m = folium.Map(location=[39.6, -8.1], zoom_start=6, control_scale=True, tiles=None)

# Esri World Imagery (satélite)
folium.TileLayer(
    tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attr="Tiles © Esri — Source: Esri, Maxar, Earthstar Geographics, and the GIS User Community",
    name="Imagem (Esri)",
    overlay=False,
    control=False,
).add_to(m)

# Labels (Carto - Positron only labels) por cima da imagem
folium.TileLayer(
    tiles="https://{s}.basemaps.cartocdn.com/light_only_labels/{z}/{x}/{y}.png",
    attr="© OpenStreetMap contributors © CARTO",
    name="Labels",
    overlay=True,
    control=False,
).add_to(m)

# Camadas de pontos
fg_local = folium.FeatureGroup(name="Localidades", show=True)
fg_ad = folium.FeatureGroup(name="AD/HEL/ULM", show=True)

# Localidades — círculos elegantes
for _, r in localidades.iterrows():
    name = str(r.get(loc_name_col, "")).strip()
    popup = folium.Popup(name or "Localidade", max_width=350)
    folium.CircleMarker(
        location=[float(r["lat"]), float(r["lon"])],
        radius=4,
        weight=1,
        color="#2a72de",       # azul
        fill=True,
        fill_color="#8ab4ff",  # azul claro
        fill_opacity=0.9,
        opacity=1.0,
        popup=popup,
    ).add_to(fg_local)

# AD/HEL/ULM — ícone de avião
# cluster para não ficar saturado se forem muitos
cluster = MarkerCluster(name="AD/HEL/ULM")
for _, r in ad_df.iterrows():
    name = str(r.get(ad_name_col, "")).strip()
    popup = folium.Popup(name or "AD/HEL/ULM", max_width=350)
    folium.Marker(
        location=[float(r["lat"]), float(r["lon"])],
        icon=folium.Icon(color="red", icon="plane", prefix="fa"),
        popup=popup,
    ).add_to(cluster)

cluster.add_to(fg_ad)

fg_local.add_to(m)
fg_ad.add_to(m)

# Ajustar bounds a todos os pontos
all_lats = list(localidades["lat"].astype(float)) + list(ad_df["lat"].astype(float))
all_lons = list(localidades["lon"].astype(float)) + list(ad_df["lon"].astype(float))
if all_lats and all_lons:
    m.fit_bounds(bounds_from_points(all_lats, all_lons), padding=(30, 30))

# Render no centro
st_folium(m, width=1000, height=680)


