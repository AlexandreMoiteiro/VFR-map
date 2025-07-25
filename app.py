import streamlit as st
import pandas as pd
import pydeck as pdk

PONTE_DE_SOR_COORDS = (39.233333, -8.0)
ZOOM_LEVEL = 8.5

df = pd.read_csv("significant_places.csv")

if 'LatDecimal' not in df.columns or 'LonDecimal' not in df.columns:
    st.error("Ficheiro sem colunas LatDecimal/LonDecimal.")
    st.stop()

st.set_page_config(page_title="Mapa de Pontos VFR", layout="wide")
st.title("Mapa de Pontos VFR em Portugal")
st.markdown("Todos os pontos do ficheiro `significant_places.csv` apresentados no mapa. Centrado em Ponte de Sor.")

# Pesquisa simples pelo nome
search = st.text_input("Pesquisar ponto pelo nome ou código:", "")
if search:
    df = df[df["Name"].str.contains(search, case=False) | df["Code"].str.contains(search, case=False)]

with st.expander("Ver tabela dos pontos VFR"):
    st.dataframe(df[["Name", "Code", "LatDecimal", "LonDecimal"]])

layer = pdk.Layer(
    "ScatterplotLayer",
    data=df,
    get_position=["LonDecimal", "LatDecimal"],
    get_color=[200, 30, 30, 220],  # vermelho forte e opaco
    get_radius=1500,                # maior
    pickable=True
)

view_state = pdk.ViewState(
    latitude=PONTE_DE_SOR_COORDS[0],
    longitude=PONTE_DE_SOR_COORDS[1],
    zoom=ZOOM_LEVEL,
    pitch=0
)

tooltip = {
    "html": "<b>{Name}</b><br>Code: {Code}<br>Lat: {LatDecimal}<br>Lon: {LonDecimal}",
    "style": {"backgroundColor": "navy", "color": "white", "zIndex": "10000"}
}

st.pydeck_chart(
    pdk.Deck(
        map_style="mapbox://styles/mapbox/streets-v12",  # mapa mais clássico e contrastante
        layers=[layer],
        initial_view_state=view_state,
        tooltip=tooltip,
    )
)



