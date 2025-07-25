import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# Lê o ficheiro CSV (ajusta se necessário)
CSV_PATH = "significant_places.csv"
df = pd.read_csv(CSV_PATH)

# Garante que não há nulos
df["LatDecimal"] = pd.to_numeric(df["LatDecimal"], errors="coerce")
df["LonDecimal"] = pd.to_numeric(df["LonDecimal"], errors="coerce")
df = df.dropna(subset=["LatDecimal", "LonDecimal"])

# Filtro de pesquisa
search = st.text_input("Filtra por nome ou código", "")
if search:
    df = df[df['Name'].str.contains(search, case=False) | df['Code'].str.contains(search, case=False)]

st.title("Significant VFR Points in Portugal")
st.write(f"Total de pontos no mapa: {len(df)}")

with st.expander("Show Data Table"):
    st.dataframe(df[['Name', 'Code', 'LatDecimal', 'LonDecimal']])

# Cria o mapa centrado em Portugal
m = folium.Map(
    location=[df["LatDecimal"].mean(), df["LonDecimal"].mean()],
    zoom_start=6,
    tiles="OpenStreetMap"
)

# Adiciona todos os pontos ao mapa
for _, row in df.iterrows():
    folium.CircleMarker(
        location=[row["LatDecimal"], row["LonDecimal"]],
        radius=4,
        fill=True,
        color="red",
        fill_opacity=0.7,
        tooltip=f"{row['Name']} ({row['Code']})<br>Lat: {row['LatDecimal']}<br>Lon: {row['LonDecimal']}"
    ).add_to(m)

# Mostra o mapa interativo no Streamlit
st_folium(m, width=800, height=600)



