import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

# Configuração do Streamlit
st.set_page_config(page_title="VFR Points Map", layout="wide")

st.title("Mapa Interativo de Pontos VFR e Áreas de Treino (Little Navmap)")

# Upload ou leitura do ficheiro
uploaded_file = st.file_uploader("Faz upload do teu ficheiro LittleNavmap.csv", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file, sep=';', encoding='utf-8')
else:
    # Para testes locais, descomenta e coloca o path correto
    # df = pd.read_csv("LittleNavmap.csv", sep=';', encoding='utf-8')
    st.warning("Por favor, faz upload do ficheiro CSV exportado do Little Navmap.")
    st.stop()

# --- Ajuste automático das colunas ---
# Se souberes os nomes exatos das colunas de latitude e longitude, altera aqui
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
    # Personaliza popup com todas as colunas, se quiseres
    popup_text = "<br>".join([f"<b>{k}:</b> {v}" for k, v in popup_info.items()])
    folium.Marker(
        location=[lat, lon],
        popup=folium.Popup(popup_text, max_width=350),
        tooltip=nome
    ).add_to(marker_cluster)

# Mostra o mapa no Streamlit
st_data = st_folium(m, width=1200, height=700)

st.info("Este mapa usa os pontos do ficheiro exportado do Little Navmap. "
        "Podes filtrar/selecionar outros tipos no CSV, ou personalizar o popup.")

