import streamlit as st
import pandas as pd
import leafmap.foliumap as leafmap

# Carregar CSV
CSV_PATH = "significant_places.csv"
df = pd.read_csv(CSV_PATH)

# Limpa e converte coordenadas
df["LatDecimal"] = pd.to_numeric(df["LatDecimal"], errors="coerce")
df["LonDecimal"] = pd.to_numeric(df["LonDecimal"], errors="coerce")
df = df.dropna(subset=["LatDecimal", "LonDecimal"])

# Filtro por nome/código
search = st.text_input("Filtra por nome ou código", "")
if search:
    df = df[df["Name"].str.contains(search, case=False) | df["Code"].str.contains(search, case=False)]

st.title("Significant VFR Points in Portugal")
st.write(f"Total de pontos no mapa: {len(df)}")

with st.expander("Ver tabela de dados"):
    st.dataframe(df[['Name', 'Code', 'LatDecimal', 'LonDecimal']])

# Cria o mapa
m = leafmap.Map(
    center=[df.LatDecimal.mean(), df.LonDecimal.mean()],
    zoom=6,
    draw_control=False,
    measure_control=False,
    fullscreen_control=True,
    locate_control=False,
    layers_control=True,
    # Experimenta outros: "CartoDB.DarkMatter", "Esri.WorldImagery", "CartoDB.Positron", etc
    basemap="CartoDB.Positron"
)

# Adiciona pontos (cluster automático!)
m.add_points_from_xy(
    df,
    x="LonDecimal",
    y="LatDecimal",
    popup=["Name", "Code", "LatDecimal", "LonDecimal"],
    icon_colors="red"
)

# Mostra no Streamlit
m.to_streamlit(height=650, width=950)




