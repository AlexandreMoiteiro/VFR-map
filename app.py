import streamlit as st
import pandas as pd
import leafmap.foliumap as leafmap

st.set_page_config(layout="wide")

st.title("🛩️ Significant VFR Points in Portugal")
st.markdown("Mapa interativo moderno dos principais pontos VFR em Portugal para navegação visual.")

# Lê o CSV
df = pd.read_csv("significant_places.csv")
df["LatDecimal"] = pd.to_numeric(df["LatDecimal"], errors="coerce")
df["LonDecimal"] = pd.to_numeric(df["LonDecimal"], errors="coerce")
df = df.dropna(subset=["LatDecimal", "LonDecimal"])

# Filtro no topo
search = st.text_input("Filtra por nome ou código VFR:", key="filtro_nome")
if search:
    df = df[df['Name'].str.contains(search, case=False) | df['Code'].str.contains(search, case=False)]

# Cria o mapa com tiles Esri (moderno e rápido)
m = leafmap.Map(
    center=[df["LatDecimal"].mean(), df["LonDecimal"].mean()],
    zoom=6.3,
    tiles="Esri.WorldTopoMap",  # ou 'Stamen.Terrain', 'OpenTopoMap', etc
    draw_control=False,
    measure_control=True,
    fullscreen_control=True,
    attribution_control=True
)

# Clustering ativado nativamente
m.add_points_from_xy(
    df,
    x="LonDecimal",
    y="LatDecimal",
    popup=["Name", "Code", "LatDecimal", "LonDecimal"],
    icon_colors="blue",   # ou personaliza por prefixo se quiseres
    cluster=True,
    layer_name="VFR Points"
)

# Mostra o mapa interativo
m.to_streamlit(height=750)

with st.expander("Ver tabela de pontos VFR"):
    st.dataframe(df[['Name', 'Code', 'LatDecimal', 'LonDecimal']])




