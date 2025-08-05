import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import re

# --- Função para converter DMS para decimal ---
def dms_to_decimal(coord):
    """Converte coordenadas do tipo DDMMSSN/DDMMSSS para decimal."""
    if pd.isnull(coord): return None
    coord = str(coord).strip()
    match = re.match(r'(\d{2,3})(\d{2})(\d{2})([NSEW])', coord)
    if not match: return None
    d, m, s, hemi = match.groups()
    decimal = int(d) + int(m)/60 + int(s)/3600
    if hemi in 'SW': decimal = -decimal
    return decimal

# --- Lê os ficheiros CSV (caminhos iguais aos de upload) ---
localidades = pd.read_csv("Localidades-Nova-versao-230223.csv")
ad_df = pd.read_csv("AD-HEL-ULM.csv")

# --- Descobre os nomes certos das colunas (pode ser diferente dependendo da extração!) ---
# Localidades: Nome da localidade e coordenadas
loc_cols = [c.upper() for c in localidades.columns]
if 'LOCALIDADE' in loc_cols:
    loc_name_col = 'LOCALIDADE'
elif 'Nome' in localidades.columns:
    loc_name_col = 'Nome'
else:
    loc_name_col = localidades.columns[0]

if 'COORDENADAS' in loc_cols:
    loc_coord_col = 'COORDENADAS'
elif 'Coordenadas' in localidades.columns:
    loc_coord_col = 'Coordenadas'
else:
    loc_coord_col = localidades.columns[1]

# ADs: Nome, identificador, tipo, latitude, longitude
ad_cols = [c.upper() for c in ad_df.columns]
def col_match(df, options):
    for o in options:
        if o in df.columns:
            return o
        if o.upper() in [c.upper() for c in df.columns]:
            return [c for c in df.columns if c.upper() == o.upper()][0]
    return df.columns[0]

ad_name_col = col_match(ad_df, ['NOME', 'Nome', 'DESIGNAÇÃO', 'Designação'])
ad_ident_col = col_match(ad_df, ['IDENT', 'ID', 'INDICATIVO'])
ad_tipo_col = col_match(ad_df, ['TIPO', 'Tipo', 'TYPE', 'Type'])
ad_lat_col = col_match(ad_df, ['LATITUDE', 'LAT', 'Latitude'])
ad_lon_col = col_match(ad_df, ['LONGITUDE', 'LON', 'Longitude'])

# --- Processa coordenadas ---
# Para Localidades (normalmente uma coluna com as duas coordenadas separadas por espaço)
def split_coords(x):
    if pd.isnull(x): return (None, None)
    x = str(x).replace('\u200b', '').replace('\n', ' ')
    parts = x.strip().split()
    if len(parts) >= 2:
        return parts[0], parts[1]
    return (None, None)
localidades[['LAT_RAW', 'LON_RAW']] = localidades[loc_coord_col].apply(lambda x: pd.Series(split_coords(x)))
localidades['LatDecimal'] = localidades['LAT_RAW'].apply(dms_to_decimal)
localidades['LonDecimal'] = localidades['LON_RAW'].apply(dms_to_decimal)
localidades = localidades.dropna(subset=['LatDecimal', 'LonDecimal'])

# Para ADs/Helis/ULM (duas colunas separadas)
ad_df['LatDecimal'] = ad_df[ad_lat_col].apply(dms_to_decimal)
ad_df['LonDecimal'] = ad_df[ad_lon_col].apply(dms_to_decimal)
ad_df = ad_df.dropna(subset=['LatDecimal', 'LonDecimal'])

# Classifica o tipo em três classes para ícone
def classify_tipo(t):
    t = str(t).lower()
    if 'heli' in t:
        return 'Heliporto'
    elif 'ulm' in t:
        return 'ULM'
    else:
        return 'Aeródromo'
ad_df['TIPO_NORM'] = ad_df[ad_tipo_col].apply(classify_tipo)

# --- APP STREAMLIT ---
st.set_page_config(page_title="VFR & Aeródromos Portugal", layout="wide")

st.markdown("""
    <style>
        .stApp { background-color: #fafbfc; }
        .folium-map { border-radius: 16px; box-shadow: 0 2px 16px #e2e2e2; }
        .stTextInput > div > div > input {font-size: 1.15em; text-align: center;}
    </style>
""", unsafe_allow_html=True)

st.markdown(
    "<h1 style='text-align:center;'>VFR Points & Aeródromos / Helis / ULM Portugal</h1>",
    unsafe_allow_html=True,
)

cols = st.columns([2, 5, 2])
with cols[1]:
    search = st.text_input("Filtrar por nome/código/localidade", "")

# Filtro nos dois conjuntos de dados
if search:
    localidades_f = localidades[localidades[loc_name_col].str.contains(search, case=False, na=False)]
    ad_f = ad_df[
        ad_df[ad_name_col].str.contains(search, case=False, na=False) |
        ad_df[ad_ident_col].astype(str).str.contains(search, case=False, na=False)
    ]
else:
    localidades_f = localidades
    ad_f = ad_df

st.markdown(
    f"<div style='text-align:center; font-size:17px; color:#888; margin-bottom:10px;'>"
    f"Localidades/Pontos: <b>{len(localidades_f)}</b> &nbsp; | &nbsp; AD/Heli/ULM: <b>{len(ad_f)}</b></div>",
    unsafe_allow_html=True,
)

# --- Mapa híbrido ESRI + labels ---
CENTER_PT = [39.7, -8.1]
m = folium.Map(
    location=CENTER_PT,
    zoom_start=7,
    tiles=None,
    control_scale=True
)
# Híbrido Esri
folium.TileLayer(
    tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attr="Esri",
    name="Esri Satellite",
    overlay=False,
    control=False
).add_to(m)
folium.TileLayer(
    tiles="https://services.arcgisonline.com/arcgis/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}",
    attr="Esri Labels",
    name="Labels",
    overlay=True,
    control=False
).add_to(m)

# --- Pontos VFR/localidades: círculo amarelo ---
for _, row in localidades_f.iterrows():
    folium.CircleMarker(
        location=[row['LatDecimal'], row['LonDecimal']],
        radius=5,
        fill=True,
        color="#fff",
        fill_color="#FFB300",  # Amarelo laranja
        fill_opacity=0.88,
        weight=1.5,
        tooltip=row[loc_name_col],
        popup=f"<b>{row[loc_name_col]}</b>",
    ).add_to(m)

# --- Aeródromos/Helis/ULM: ícone distinto por tipo ---
for _, row in ad_f.iterrows():
    if row['TIPO_NORM'] == 'Aeródromo':
        icon = folium.Icon(color='blue', icon='plane', prefix='fa')
    elif row['TIPO_NORM'] == 'Heliporto':
        icon = folium.Icon(color='green', icon='helicopter', prefix='fa')
    elif row['TIPO_NORM'] == 'ULM':
        icon = folium.Icon(color='red', icon='flag', prefix='fa')
    else:
        icon = folium.Icon(color='gray')
    folium.Marker(
        location=[row['LatDecimal'], row['LonDecimal']],
        icon=icon,
        tooltip=f"{row[ad_name_col]} ({row[ad_ident_col]})",
        popup=f"<b>{row[ad_name_col]}</b><br>{row[ad_ident_col]}<br>{row['TIPO_NORM']}",
    ).add_to(m)

# Centraliza o mapa na página
map_cols = st.columns([0.1, 0.8, 0.1])
with map_cols[1]:
    st_folium(m, width=1100, height=650)

with st.expander("Ver tabela de localidades/pontos VFR"):
    st.dataframe(localidades_f[[loc_name_col, loc_coord_col, 'LatDecimal', 'LonDecimal']], use_container_width=True)
with st.expander("Ver tabela de Aeródromos/Helis/ULM"):
    st.dataframe(ad_f[[ad_ident_col, ad_name_col, ad_tipo_col, ad_lat_col, ad_lon_col, 'LatDecimal', 'LonDecimal']], use_container_width=True)




