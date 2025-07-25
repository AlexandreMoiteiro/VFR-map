import streamlit as st
import pandas as pd
import leafmap.foliumap as leafmap
from datetime import datetime

# --- PAGE SETUP ---
st.set_page_config(layout="wide", page_title="VFR Map Portugal", page_icon="🛩️")

# --- STYLE: GLOBAL STREAMLIT ---
st.markdown("""
<style>
html, body, [class*="css"] { background-color: #f5f6fa !important; }
h1, h2, h3 { color: #0a1128 !important; }
.folium-map {border-radius: 18px; box-shadow: 0 2px 20px #bfc9da;}
.stButton>button { border-radius: 8px; font-weight: 600;}
.stTextInput>div>div>input {border-radius: 8px;}
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.title("🛩️ Significant VFR Points Portugal")
st.caption("Mapa interativo de pontos VFR para navegação visual em Portugal. Clique nos pontos para detalhes.")

# --- LER CSV E PREPARAR DADOS ---
df = pd.read_csv("significant_places.csv")
df["LatDecimal"] = pd.to_numeric(df["LatDecimal"], errors="coerce")
df["LonDecimal"] = pd.to_numeric(df["LonDecimal"], errors="coerce")
df = df.dropna(subset=["LatDecimal", "LonDecimal"])

# --- FILTRO RÁPIDO ---
col1, col2, col3 = st.columns([1,2,1])
with col2:
    search = st.text_input("🔎 Procurar por nome ou código VFR:", "", placeholder="ex: LAVRA ou LAVAD")
    base_map = st.selectbox("🗺️ Estilo do mapa", [
        "CartoDB.Positron", "Esri.WorldTopoMap", "Stamen.Terrain", "OpenTopoMap", "CartoDB.DarkMatter"
    ], index=0, help="Escolhe o fundo do mapa")

if search:
    df = df[df['Name'].str.contains(search, case=False) | df['Code'].str.contains(search, case=False)]

st.markdown(f"<b>Total de pontos no mapa:</b> {len(df)}", unsafe_allow_html=True)

# --- PALETA DE CORES POR PREFIXO (clean e moderna) ---
def code_color(code):
    prefix = code[:2].upper()
    color_dict = {
        'AB': '#2979ff', 'AL': '#00bfae', 'AM': '#ffb300', 'BA': '#7e57c2',
        'BE': '#e65100', 'CA': '#d7263d', 'CO': '#61a5c2', 'EV': '#e84855',
        'FA': '#43a047', 'PO': '#6d4c41', 'SE': '#00838f', 'VI': '#0a1128', 'MA': '#a5d8ff'
    }
    return color_dict.get(prefix, "#2e3a4f")

# --- CRIAR MAPA ---
center = [df["LatDecimal"].mean(), df["LonDecimal"].mean()]
m = leafmap.Map(
    center=center,
    zoom=6.3,
    tiles=base_map,
    draw_control=False,
    measure_control=True,
    fullscreen_control=True,
    attribution_control=False
)

# --- ADD PONTOS (cluster com cores) ---
features = []
for _, row in df.iterrows():
    cor = code_color(row["Code"])
    html = f"""
    <div style='font-family:Montserrat,sans-serif;font-size:15px;'>
      <b>{row['Name']}</b> <br>
      <b>Code:</b> <span style='color:{cor}'>{row['Code']}</span><br>
      <b>Lat:</b> {row['LatDecimal']:.5f} <b>Lon:</b> {row['LonDecimal']:.5f}
    </div>
    """
    features.append({
        "geometry": {
            "type": "Point",
            "coordinates": [row['LonDecimal'], row['LatDecimal']]
        },
        "type": "Feature",
        "properties": {
            "popup": html,
            "style": {
                "color": cor,
                "fillColor": cor,
                "radius": 8,
                "weight": 2,
                "fillOpacity": 0.85
            }
        }
    })

import geojson
geojson_obj = geojson.FeatureCollection(features)

# Adiciona camada de pontos clusterizados
m.add_geojson(
    geojson_obj,
    layer_name="VFR Points",
    marker_type="circle",
    cluster=True,
    zoom_to_layer=False,
)

# --- CONTROLOS MODERNOS ---
m.add_minimap()
m.add_layer_control()

# --- MOSTRA MAPA ---
m.to_streamlit(height=680, width=1100)

# --- TABELA EM EXPANDER (visual e limpa) ---
with st.expander("Ver tabela dos pontos VFR"):
    st.dataframe(
        df[['Name', 'Code', 'LatDecimal', 'LonDecimal']],
        use_container_width=True,
        hide_index=True
    )

# --- FOOTER CLEAN ---
st.markdown(
    f"<div style='text-align:right; font-size:13px; color:#888;'>© {datetime.now().year} | Desenvolvido por OpenAI GPT · Design clean · Leafmap</div>",
    unsafe_allow_html=True
)





