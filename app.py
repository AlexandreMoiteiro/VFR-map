import streamlit as st
import pandas as pd
from streamlit_folium import st_folium
import folium

# ======================
# 1. Carregar os dados
# ======================
data = """
Name,Latitude,LatDir,Longitude,LonDir,Code,LatDecimal,LonDecimal
Abrantes,3927,N,00811,W,ABRAN,39.45,-8.183333
Academia Militar Lisboa,3843,N,00908,W,ACMIL,38.716667,-9.133333
Agucadoura,4125,N,00846,W,AGUSA,41.416667,-8.766667
Aguda,4102,N,00839,W,AGUDA,41.033333,-8.65
Agueda,4034,N,00826,W,AGUED,40.566667,-8.433333
Aguieira,4020,N,00811,W,AGUIE,40.333333,-8.183333
...
Vouzela,4043,N,00806,W,VIELA,40.716667,-8.1
"""  # cole todos os dados aqui!

from io import StringIO
df = pd.read_csv(StringIO(data))

# ===========================
# 2. Definir o centro do mapa
# ===========================
lat_centro = df['LatDecimal'].mean()
lon_centro = df['LonDecimal'].mean()

# =======================
# 3. Criar o mapa Folium
# =======================
m = folium.Map(location=[lat_centro, lon_centro], zoom_start=7, tiles="OpenStreetMap")

# Adicionar pontos ao mapa
for idx, row in df.iterrows():
    popup = f"<b>{row['Name']}</b><br>Código: {row['Code']}<br>Lat: {row['LatDecimal']}<br>Lon: {row['LonDecimal']}"
    folium.Marker(
        location=[row['LatDecimal'], row['LonDecimal']],
        popup=popup,
        icon=folium.Icon(color="blue", icon="info-sign"),
    ).add_to(m)

# ===========================
# 4. Mostrar no Streamlit App
# ===========================
st.title("Mapa Interativo de Pontos VFR")
st.write(
    "Visualize todos os pontos VFR do país num mapa interativo. Clique nos marcadores para detalhes."
)
st_folium(m, width=900, height=600)


