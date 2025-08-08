import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import re

st.set_page_config(page_title="VFR & Aeródromos Portugal", layout="wide")

# ---------- Utilidades ----------
def dms_to_decimal(coord: str):
    """Converte DMS tipo '404903N' ou '0073211W' para decimal."""
    if coord is None or (isinstance(coord, float) and pd.isna(coord)):
        return None
    coord = str(coord).strip().replace(" ", "")
    m = re.match(r"^(\d{2,3})(\d{2})(\d{2})([NSEW])$", coord)
    if not m:
        return None
    d, mnt, s, hemi = m.groups()
    val = int(d) + int(mnt)/60 + int(s)/3600
    if hemi in ("S", "W"):
        val = -val
    return val

def find_col(df, candidates):
    for c in candidates:
        if c in df.columns:
            return c
    return None

def build_lat_lon_from_any(df, single_coord_candidates, lat_candidates, lon_candidates):
    """
    Cria LatDecimal/LonDecimal a partir de:
      A) uma única coluna com 'LAT LON' (ex: '404903N 0073211W'), ou
      B) duas colunas LAT / LON em DMS.
    """
    # Tenta A) coluna única
    coord_col = find_col(df, single_coord_candidates)
    if coord_col:
        def split_coords(x):
            if pd.isna(x):
                return (None, None)
            parts = str(x).strip().split()
            if len(parts) >= 2:
                return (parts[0], parts[1])
            # às vezes vêm coladas sem espaço: tenta cortar pelo hemisfério
            s = str(x).strip().upper()
            s = s.replace("\u200b", "")
            # procura o primeiro N/S para separar latitude
            idx = max(s.find("N"), s.find("S"))
            if idx != -1:
                lat = s[:idx+1]
                lon = s[idx+1:].strip()
                return (lat, lon) if lon else (lat, None)
            return (None, None)

        df[["__LAT_RAW", "__LON_RAW"]] = df[coord_col].apply(lambda v: pd.Series(split_coords(v)))
        df["LatDecimal"] = df["__LAT_RAW"].apply(dms_to_decimal)
        df["LonDecimal"] = df["__LON_RAW"].apply(dms_to_decimal)
        return df

    # Tenta B) colunas separadas
    lat_col = find_col(df, lat_candidates)
    lon_col = find_col(df, lon_candidates)
    if lat_col and lon_col:
        df["LatDecimal"] = df[lat_col].apply(dms_to_decimal)
        df["LonDecimal"] = df[lon_col].apply(dms_to_decimal)
        return df

    # Se nada encontrado, não cria colunas (iremos avisar no UI)
    return df

# ---------- Carregar dados ----------
# Ajusta os nomes dos ficheiros se necessário
LOCALIDADES_CSV = "Localidades-Nova-versao-230223.csv"
AD_CSV          = "AD-HEL-ULM.csv"

localidades = pd.read_csv(LOCALIDADES_CSV)
ad_df        = pd.read_csv(AD_CSV)

# Normaliza cabeçalhos
localidades.columns = [c.strip().upper() for c in localidades.columns]
ad_df.columns       = [c.strip().upper() for c in ad_df.columns]

# ---------- Preparar Localidades (VFR points) ----------
localidades = build_lat_lon_from_any(
    localidades,
    single_coord_candidates=["COORDENADAS", "COORD", "COORDS"],
    lat_candidates=["LATITUDE", "LAT", "LAT_DMS", "LAT DMS"],
    lon_candidates=["LONGITUDE", "LON", "LON_DMS", "LON DMS"]
)

# Só depois de tentar criar as colunas é que validamos:
if "LatDecimal" not in localidades.columns or "LonDecimal" not in localidades.columns:
    st.error("Não encontrei colunas de coordenadas em **Localidades**. "
             "Assegura-te que existe 'COORDENADAS' (com 'LAT LON') ou 'LATITUDE' e 'LONGITUDE' em DMS.")
    st.write("Colunas detetadas em Localidades:", list(localidades.columns))
    st.stop()

localidades = localidades.dropna(subset=["LatDecimal", "LonDecimal"])

# Nome da localidade (tentamos várias possibilidades)
name_loc_col = find_col(localidades, ["LOCALIDADE", "NAME", "NOME"]) or localidades.columns[0]

# ---------- Preparar AD / Heli / ULM ----------
# Identifica colunas principais
ident_col = find_col(ad_df, ["IDENT", "IDENTIFICADOR", "ID", "INDICATIVO"]) or ad_df.columns[0]
name_col  = find_col(ad_df, ["NOME", "NAME", "DESIGNAÇÃO"]) or ad_df.columns[1]
tipo_col  = find_col(ad_df, ["TIPO", "TYPE", "CATEGORIA"]) or ad_df.columns[-1]

ad_df = build_lat_lon_from_any(
    ad_df,
    single_coord_candidates=["COORDENADAS", "COORD", "COORDS"],
    lat_candidates=["LATITUDE", "LAT", "LAT_DMS", "LAT DMS"],
    lon_candidates=["LONGITUDE", "LON", "LON_DMS", "LON DMS"]
)

if "LatDecimal" not in ad_df.columns or "LonDecimal" not in ad_df.columns:
    st.error("Não encontrei colunas de coordenadas em **AD/HEL/ULM**. "
             "Assegura-te que existe 'COORDENADAS' (com 'LAT LON') ou 'LATITUDE' e 'LONGITUDE' em DMS.")
    st.write("Colunas detetadas em AD/HEL/ULM:", list(ad_df.columns))
    st.stop()

ad_df = ad_df.dropna(subset=["LatDecimal", "LonDecimal"])

def classify_tipo(t):
    t = str(t).lower()
    if "heli" in t:
        return "Heliporto"
    if "ulm" in t:
        return "ULM"
    return "Aeródromo"

ad_df["TIPO_NORM"] = ad_df[tipo_col].apply(classify_tipo)

# ---------- UI ----------
st.markdown("""
<style>
    .stApp { background-color: #fafbfc; }
    .folium-map { border-radius: 16px; box-shadow: 0 2px 16px #e2e2e2; }
    .stTextInput > div > div > input {font-size: 1.05em; text-align: center;}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align:center;'>VFR Points & Aeródromos / Helis / ULM Portugal</h1>", unsafe_allow_html=True)

mid = st.columns([2,5,2])[1]
with mid:
    search = st.text_input("Filtrar por nome/código/localidade", "")

# Filtros
if search:
    localidades_f = localidades[localidades[name_loc_col].astype(str).str.contains(search, case=False, na=False)]
    ad_f = ad_df[
        ad_df[name_col].astype(str).str.contains(search, case=False, na=False) |
        ad_df[ident_col].astype(str).str.contains(search, case=False, na=False)
    ]
else:
    localidades_f = localidades
    ad_f = ad_df

st.markdown(
    f"<div style='text-align:center; color:#666;'>"
    f"Localidades/Pontos: <b>{len(localidades_f)}</b> &nbsp; | &nbsp; AD/Heli/ULM: <b>{len(ad_f)}</b>"
    f"</div>", unsafe_allow_html=True
)

# ---------- Mapa (Esri híbrido) ----------
CENTER_PT = [39.7, -8.1]
m = folium.Map(location=CENTER_PT, zoom_start=7, tiles=None, control_scale=True)
folium.TileLayer(
    tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attr="Esri", name="Esri Satellite", overlay=False, control=False
).add_to(m)
folium.TileLayer(
    tiles="https://services.arcgisonline.com/arcgis/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}",
    attr="Esri Labels", name="Labels", overlay=True, control=False
).add_to(m)

# Localidades (círculos amarelos com contorno branco)
for _, r in localidades_f.iterrows():
    folium.CircleMarker(
        location=[r["LatDecimal"], r["LonDecimal"]],
        radius=5,
        fill=True,
        color="#ffffff",
        fill_color="#FFB300",
        fill_opacity=0.9,
        weight=1.5,
        tooltip=str(r[name_loc_col]),
        popup=f"<b>{r[name_loc_col]}</b>",
    ).add_to(m)

# AD / Helis / ULM
for _, r in ad_f.iterrows():
    if r["TIPO_NORM"] == "Aeródromo":
        icon = folium.Icon(color="blue", icon="plane", prefix="fa")
    elif r["TIPO_NORM"] == "Heliporto":
        icon = folium.Icon(color="green", icon="helicopter", prefix="fa")
    else:  # ULM
        icon = folium.Icon(color="red", icon="flag", prefix="fa")

    folium.Marker(
        location=[r["LatDecimal"], r["LonDecimal"]],
        icon=icon,
        tooltip=f"{r[name_col]} ({r[ident_col]})",
        popup=f"<b>{r[name_col]}</b><br>{r[ident_col]}<br>{r['TIPO_NORM']}",
    ).add_to(m)

# Centralizar visualmente o mapa
c = st.columns([0.07, 0.86, 0.07])[1]
with c:
    st_folium(m, width=1200, height=680)

with st.expander("Tabela — Localidades/Pontos VFR"):
    cols_show = [col for col in [name_loc_col, "COORDENADAS", "LATITUDE", "LONGITUDE", "LatDecimal", "LonDecimal"] if col in localidades_f.columns]
    st.dataframe(localidades_f[cols_show], use_container_width=True)

with st.expander("Tabela — AD / Heli / ULM"):
    cols_show2 = [col for col in [ident_col, name_col, tipo_col, "COORDENADAS", "LATITUDE", "LONGITUDE", "LatDecimal", "LonDecimal"] if col in ad_f.columns]
    st.dataframe(ad_f[cols_show2], use_container_width=True)




