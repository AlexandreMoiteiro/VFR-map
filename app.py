import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

st.set_page_config(page_title="Mapa Pontos VFR Portugal", layout="wide")
st.title("Mapa Interativo de Pontos VFR, Áreas de Treino e Aeródromos (Little Navmap)")

CSV_PATH = "LittleNavmap.csv"  # ou "/mnt/data/LittleNavmap.csv"

# ----------- Lê o ficheiro só uma vez ------------
@st.cache_data
def carregar_pontos(csv_path):
    df = pd.read_csv(csv_path, sep=',', encoding='utf-8', header=None)
    pontos = []
    for i, row in df.iterrows():
        ponto = {
            'tipo': str(row[0]).strip().upper(),   # VRP, etc
            'nome': str(row[1]).strip(),
            'codigo': str(row[2]).strip(),
            'lat': float(row[3]),
            'lon': float(row[4])
        }
        pontos.append(ponto)
    return pontos

pontos = carregar_pontos(CSV_PATH)

# ----------- Filtro pelo tipo (ex: só VRP) -----------
tipos_disponiveis = sorted(set(p['tipo'] for p in pontos))
tipo_selecionado = st.selectbox("Filtrar por tipo de ponto", ["TODOS"] + tipos_disponiveis)

if tipo_selecionado == "TODOS":
    pontos_a_mostrar = pontos
else:
    pontos_a_mostrar = [p for p in pontos if p['tipo'] == tipo_selecionado]

st.write(f"Total de pontos mostrados: {len(pontos_a_mostrar)}")

# ----------- Criação do mapa -----------
# Centrado aproximadamente em Ponte de Sor
m = folium.Map(location=[39.2117, -8.0579], zoom_start=8, tiles="OpenStreetMap")
marker_cluster = MarkerCluster().add_to(m)

for ponto in pontos_a_mostrar:
    popup_text = (
        f"<b>Nome:</b> {ponto['nome']}<br>"
        f"<b>Código:</b> {ponto['codigo']}<br>"
        f"<b>Tipo:</b> {ponto['tipo']}<br>"
        f"<b>Latitude:</b> {ponto['lat']}<br>"
        f"<b>Longitude:</b> {ponto['lon']}"
    )
    folium.Marker(
        location=[ponto['lat'], ponto['lon']],
        popup=folium.Popup(popup_text, max_width=350),
        tooltip=f"{ponto['nome']} ({ponto['codigo']})"
    ).add_to(marker_cluster)

st_folium(m, width=1200, height=700)

st.caption("Dados lidos automaticamente do LittleNavmap.csv. "
           "Para atualizar pontos, basta substituir o ficheiro.")


