import streamlit as st
import pandas as pd
import pydeck as pdk

# Coordenadas de Ponte de Sor
PONTE_DE_SOR_COORDS = (39.233333, -8.0)
ZOOM_LEVEL = 8.5  # Zoom recomendado para ver bem Portugal inteiro, mas centrado em Ponte de Sor

# Ler o ficheiro csv (tem de estar na mesma pasta)
df = pd.read_csv("significant_places.csv")

# Garantir que as colunas decimais existem
if 'LatDecimal' not in df.columns or 'LonDecimal' not in df.columns:
    st.error("Ficheiro sem colunas LatDecimal/LonDecimal.")
    st.stop()

# Se quiseres mostrar só alguns pontos (ex: área de treino), podes filtrar aqui
# Exemplo: df = df[df["Tipo"] == "VFR"]

st.set_page_config(page_title="Mapa de Pontos VFR", layout="wide")
st.title("Mapa de Pontos VFR em Portugal")
st.markdown("Todos os pontos do ficheiro `significant_places.csv` apresentados no mapa. Centrado em Ponte de Sor.")

# Mostrar tabela (opcional)
with st.expander("Ver tabela dos pontos VFR"):
    st.dataframe(df[["Name", "Code", "LatDecimal", "LonDecimal"]])

# Layer dos marcadores no mapa
layer = pdk.Layer(
    "ScatterplotLayer",
    data=df,
    get_position=["LonDecimal", "LatDecimal"],
    get_color=[230, 57, 70, 180],  # cor vermelha semi-transparente
    get_radius=600,
    pickable=True
)

# Vista inicial do mapa
view_state = pdk.ViewState(
    latitude=PONTE_DE_SOR_COORDS[0],
    longitude=PONTE_DE_SOR_COORDS[1],
    zoom=ZOOM_LEVEL,
    pitch=0
)

# Tooltip customizado
tooltip = {
    "html": "<b>{Name}</b><br>Code: {Code}<br>Lat: {LatDecimal}<br>Lon: {LonDecimal}",
    "style": {"backgroundColor": "steelblue", "color": "white"}
}

# Mostrar mapa
st.pydeck_chart(
    pdk.Deck(
        map_style="mapbox://styles/mapbox/light-v9",
        layers=[layer],
        initial_view_state=view_state,
        tooltip=tooltip,
    )
)



