import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

st.set_page_config(page_title="VFR Points Map", layout="wide")
st.title("Mapa Interativo de Pontos VFR e Áreas de Treino (Little Navmap)")

# Carrega sempre o ficheiro fornecido
CSV_PATH = "LittleNavmap.csv"  # Garante que o nome está igual ao ficheiro

# Lê o CSV
try:
    df = pd.read_csv(CSV_PATH, sep=';', encoding='utf-8')
except Exception as e:
    st.error(f"Erro a abrir o ficheiro: {e}")
    st.stop()

# Identifica as colunas de latitude, longitude e nome
lat_col = [col for col in df.columns if 'lat' in col.lower()][0]
lon_col = [col for col in df.columns if 'lon' in col.lower() or 'lng' in col.lower()][0]
name_col = [col for col in df.columns if 'name' in col.lower()][0]

# Cria o mapa centrado em Ponte de Sor
m = folium.Map(location=[39.2117, -8.0579], zoom_start=9, tiles="OpenStreetMap")
marker_cluster = MarkerCluster().add_to(m)

for idx, row in df.iterrows():
    lat = row[lat_col]
    lon = row[lon_col]
    nome = row[name_col]
    popup_info = row.to_dict()
    popup_text = "<br>".join([f"<b>{k}:</b> {v}" for k, v in popup_info.items()])
    folium.Marker(
        location=[lat, lon],
        popup=folium.Popup(popup_text, max_width=350),
        tooltip=nome
    ).add_to(marker_cluster)

st_folium(m, width=1200, height=700)


