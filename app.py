import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import tabula
import re

# ---------- FUNÇÕES AUXILIARES ----------

def dms_to_decimal(coord):
    """Converte coordenadas tipo DDMMSSN/DDMMSSS para decimal."""
    if pd.isnull(coord): return None
    coord = coord.strip()
    match = re.match(r'(\d{2,3})(\d{2})(\d{2})([NSEW])', coord)
    if not match: return None
    d, m, s, hemi = match.groups()
    decimal = int(d) + int(m)/60 + int(s)/3600
    if hemi in 'SW': decimal = -decimal
    return decimal

# ---------- EXTRAÇÃO E PROCESSAMENTO DOS PDFs ----------

# Extrair tabela de localidades (pontos VFR) do PDF
localidades_pdf = "Localidades-Nova-versao-230223.pdf"
localidades_tables = tabula.read_pdf(localidades_pdf, pages="all", multiple_tables=True, lattice=True)

# Tenta encontrar a tabela correta (normalmente a maior com colunas 'LOCALIDADE', 'COORDENADAS', etc)
for table in localidades_tables:
    if 'COORDENADAS' in table.columns or 'Coordenadas' in table.columns:
        localidades = table
        break
else:
    localidades = localidades_tables[0]
    localidades.columns = [c.upper() for c in localidades.columns]

# Uniformizar nomes de colunas
localidades.columns = [c.upper() for c in localidades.columns]
if 'COORDENADAS' not in localidades.columns and 'Coordenadas' in localidades.columns:
    localidades.rename(columns={'Coordenadas': 'COORDENADAS'}, inplace=True)

# Processar coordenadas
def split_coords(x):
    if pd.isnull(x): return (None, None)
    x = str(x).replace('\u200b', '').replace('\n', ' ')
    parts = x.strip().split()
    if len(parts) >= 2:
        return parts[0], parts[1]
    return (None, None)
localidades[['LAT_RAW', 'LON_RAW']] = localidades['COORDENADAS'].apply(lambda x: pd.Series(split_coords(x)))
localidades['LatDecimal'] = localidades['LAT_RAW'].apply(dms_to_decimal)
localidades['LonDecimal'] = localidades['LON_RAW'].apply(dms_to_decimal)
localidades = localidades.dropna(subset=['LatDecimal', 'LonDecimal'])

# -------- Aeródromos, Helis e ULM do PDF --------
ad_pdf = "AD-HEL-ULM.pdf"
ad_tables = tabula.read_pdf(ad_pdf, pages="all", multiple_tables=True, lattice=True)

# Junta todas as tabelas (algumas podem estar divididas)
ad_df = pd.concat(ad_tables, ignore_index=True)
ad_df.columns = [c.upper() for c in ad_df.columns]

# Heurística para encontrar as colunas certas em diferentes layouts
for col in ['IDENT', 'ID', 'INDICATIVO']:
    if col in ad_df.columns:
        ident_col = col
        break
else:
    ident_col = ad_df.columns[0]
for col in ['NOME', 'NAME', 'DESIGNAÇÃO']:
    if col in ad_df.columns:
        name_col = col
        break
else:
    name_col = ad_df.columns[1]
for col in ['LATITUDE', 'LAT', 'COORDENADAS']:
    if col in ad_df.columns:
        lat_col = col
        break
else:
    lat_col = ad_df.columns[2]
for col in ['LONGITUDE', 'LON']:
    if col in ad_df.columns:
        lon_col = col
        break
else:
    lon_col = ad_df.columns[3]
for col in ['TIPO', 'TYPE']:
    if col in ad_df.columns:
        type_col = col
        break
else:
    type_col = ad_df.columns[-1]

# Processar coordenadas de aeródromos
ad_df['LatDecimal'] = ad_df[lat_col].apply(dms_to_decimal)
ad_df['LonDecimal'] = ad_df[lon_col].apply(dms_to_decimal)
ad_df = ad_df.dropna(subset=['LatDecimal', 'LonDecimal'])

# Opcional: Normalizar tipo para 3 categorias
def classify_tipo(t):
    t = str(t).lower()
    if 'heli' in t:
        return 'Heliporto'
    elif 'ulm' in t:
        return 'ULM'
    else:
        return 'Aeródromo'
ad_df['TIPO_NORM'] = ad_df[type_col].apply(classify_tipo)

# ---------- STREAMLIT APP ----------
st.set_page_config(page_title="VFR e Aeródromos Portugal", layout="wide")

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

# Filtro em ambos os datasets
if search:
    localidades_f = localidades[localidades['LOCALIDADE'].str.contains(search, case=False, na=False)]
    ad_f = ad_df[
        ad_df[name_col].str.contains(search, case=False, na=False) |
        ad_df[ident_col].astype(str).str.contains(search, case=False, na=False)
    ]
else:
    localidades_f = localidades
    ad_f = ad_df

st.markdown(
    f"<div style='text-align:center; font-size:17px; color:#888; margin-bottom:10px;'>"
    f"Localidades/Pontos: <b>{len(localidades_f)}</b> &nbsp; | &nbsp; AD/Heli/ULM: <b>{len(ad_f)}</b></div>",
    unsafe_allow_html=True,
)

# ---- MAPA HÍBRIDO, SIMBOLOS DIFERENTES ----
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

# -- Pontos VFR/localidades: círculo amarelo
for _, row in localidades_f.iterrows():
    folium.CircleMarker(
        location=[row['LatDecimal'], row['LonDecimal']],
        radius=5,
        fill=True,
        color="#fff",
        fill_color="#FFB300",  # Amarelo
        fill_opacity=0.88,
        weight=1.5,
        tooltip=row['LOCALIDADE'],
        popup=f"<b>{row['LOCALIDADE']}</b>",
    ).add_to(m)

# -- Aeródromos/Helis/ULM: símbolos diferentes
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
        tooltip=f"{row[name_col]} ({row[ident_col]})",
        popup=f"<b>{row[name_col]}</b><br>{row[ident_col]}<br>{row['TIPO_NORM']}",
    ).add_to(m)

# Centralizar mapa na página
map_cols = st.columns([0.1, 0.8, 0.1])
with map_cols[1]:
    st_folium(m, width=1100, height=650)

# Expander para tabelas dos dados
with st.expander("Ver tabela de localidades/pontos VFR"):
    st.dataframe(localidades_f[["LOCALIDADE", "COORDENADAS", "LatDecimal", "LonDecimal"]], use_container_width=True)
with st.expander("Ver tabela de Aeródromos/Helis/ULM"):
    st.dataframe(ad_f[[ident_col, name_col, type_col, lat_col, lon_col, 'LatDecimal', 'LonDecimal']], use_container_width=True)



