import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import re

# --- Função para converter DMS (DDMMSSN/W) para decimal ---
def dms_to_decimal(coord):
    if pd.isnull(coord): return None
    coord = str(coord).strip()
    match = re.match(r"(\d{2,3})(\d{2})(\d{2}(?:\.\d+)?)?([NSEW])", coord)
    if not match: return None
    d, m, s, hemi = match.groups()
    d, m = int(d), int(m)
    s = float(s) if s else 0.0
    decimal = d + m / 60 + s / 3600
    if hemi in 'SW': decimal = -decimal
    return decimal

# --- Função para descobrir o header correto ---
def find_header_row(filepath, search_terms):
    with open(filepath, encoding='utf-8') as f:
        for idx, line in enumerate(f):
            if all(term in line for term in search_terms):
                return idx
    return 0  # fallback

# --- Lê e limpa LOCALIDADES ---
localidades_file = "Localidades-Nova-versao-230223.csv"
header_row_loc = find_header_row(localidades_file, ["LOCALIDADE", "COORDENADAS"])
localidades = pd.read_fwf(localidades_file, skip_blank_lines=True, header=header_row_loc)
localidades.columns = [c.strip() for c in localidades.columns]
st.write("Colunas lidas em localidades:", localidades.columns.tolist())

# Remove linhas sem localidade ou com "Total de registos"
localidades = localidades.dropna(how='all')
if "LOCALIDADE" in localidades.columns:
    localidades = localidades[~localidades['LOCALIDADE'].astype(str).str.contains('Total de registos|nan', na=False, case=False)]
    localidades = localidades[~localidades['LOCALIDADE'].astype(str).str.strip().eq('')]
else:
    st.error("Coluna 'LOCALIDADE' não encontrada em localidades. Encontradas: " + ", ".join(localidades.columns))
    st.stop()

# --- Lê e limpa AD/HEL/ULM ---
ad_file = "AD-HEL-ULM.csv"
header_row_ad = find_header_row(ad_file, ["Ident", "Latitude", "Longitude"])
ad_df = pd.read_fwf(ad_file, skip_blank_lines=True, header=header_row_ad)
ad_df.columns = [c.strip() for c in ad_df.columns]
st.write("Colunas lidas em AD/HEL/ULM:", ad_df.columns.tolist())

ad_df = ad_df.dropna(how='all')
if "Ident" in ad_df.columns:
    ad_df = ad_df[~ad_df['Ident'].astype(str).str.contains('Coord for FPL|Ident', na=False, case=False)]
    ad_df = ad_df[~ad_df['Ident'].astype(str).str.strip().eq('')]
else:
    st.error("Coluna 'Ident' não encontrada em AD/Heli/ULM. Encontradas: " + ", ".join(ad_df.columns))
    st.stop()

# --- Variáveis para os nomes das colunas ---
loc_name_col = 'LOCALIDADE'
loc_coord_col = 'COORDENADAS'
ad_name_col = [c for c in ad_df.columns if 'Name for FPL' in c][0]
ad_ident_col = 'Ident'
ad_lat_col = 'Latitude'
ad_lon_col = 'Longitude'
ad_tipo_col = ad_name_col

# --- Processar coordenadas das localidades ---
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

# --- Processar coordenadas dos ADs/Helis/ULM ---
ad_df['LatDecimal'] = ad_df[ad_lat_col].apply(dms_to_decimal)
ad_df['LonDecimal'] = ad_df[ad_lon_col].apply(dms_to_decimal)
ad_df = ad_df.dropna(subset=['LatDecimal', 'LonDecimal'])

# --- Classifica tipo ---
def classify_tipo(nome):
    n = str(nome).lower()
    if 'heli' in n:
        return 'Heliporto'
    elif 'ulm' in n:
        return 'ULM'
    else:
        return 'Aeródromo'
ad_df['TIPO_NORM'] = ad_df[ad_tipo_col].apply(classify_tipo)

# --- STREAMLIT APP ---
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

# Filtro
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

# --- Mapa híbrido ESRI ---
CENTER_PT = [39.7, -8.1]
m = folium.Map(
    location=CENTER_PT,
    zoom_start=7,
    tiles=None,
    control_scale=True
)
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
        fill_color="#FFB300",
        fill_opacity=0.88,
        weight=1.5,
        tooltip=row[loc_name_col],
        popup=f"<b>{row[loc_name_col]}</b>",
    ).add_to(m)

# --- AD/Helis/ULM: ícone diferente ---
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

# --- Centraliza o mapa na página ---
map_cols = st.columns([0.1, 0.8, 0.1])
with map_cols[1]:
    st_folium(m, width=1100, height=650)

with st.expander("Ver tabela de localidades/pontos VFR"):
    st.dataframe(localidades_f[[loc_name_col, loc_coord_col, 'LatDecimal', 'LonDecimal']], use_container_width=True)
with st.expander("Ver tabela de Aeródromos/Helis/ULM"):
    st.dataframe(ad_f[[ad_ident_col, ad_name_col, ad_lat_col, ad_lon_col, 'LatDecimal', 'LonDecimal', 'TIPO_NORM']], use_container_width=True)



