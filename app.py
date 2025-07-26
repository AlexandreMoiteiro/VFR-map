import streamlit as st
import pandas as pd
import leafmap.foliumap as leafmap

# Config Streamlit
st.set_page_config(page_title="VFR Points Portugal", layout="wide")

st.markdown("""
    <style>
    .stApp { background: #f7f7f7; }
    h1 { text-align: center !important; }
    </style>
""", unsafe_allow_html=True)

# Lê os dados
df = pd.read_csv("significant_places.csv")
df["LatDecimal"] = pd.to_numeric(df["LatDecimal"], errors="coerce")
df["LonDecimal"] = pd.to_numeric(df["LonDecimal"], errors="coerce")
df = df.dropna(subset=["LatDecimal", "LonDecimal"])

# Título e filtro central
st.markdown("<h1 style='text-align:center;'>Significant VFR Points in Portugal</h1>", unsafe_allow_html=True)
cols = st.columns([2, 4, 2])
with cols[1]:
    search = st.text_input("Filtrar por nome ou código VFR", "")

if search:
    df = df[df['Name'].str.contains(search, case=False) | df['Code'].str.contains(search, case=False)]

st.markdown(f"<div style='text-align:center; font-size:17px; margin-bottom: 9px;'>Pontos visíveis: <b>{len(df)}</b></div>", unsafe_allow_html=True)

# Cria o mapa leafmap centrado no Continente
center = [39.7, -8.1]
m = leafmap.Map(center=center, zoom=7, tiles="CartoDB.Positron", draw_control=False, measure_control=False, fullscreen_control=False)

# Adiciona os pontos VFR (CircleMarkers) 
for _, row in df.iterrows():
    m.add_circle_marker(
        location=[row["LatDecimal"], row["LonDecimal"]],
        radius=6,
        color="#205081",         # Azul petróleo (ou troca por #EA7317, etc)
        fill_color="#205081",
        fill_opacity=0.93,
        popup=f"<b>{row['Name']}</b><br>Código: <b>{row['Code']}</b>",
        tooltip=f"{row['Name']} ({row['Code']})"
    )

# Mostra o mapa no Streamlit
m.to_streamlit(width=1200, height=630)

with st.expander("Ver tabela dos pontos mostrados no mapa"):
    st.dataframe(df[['Name', 'Code', 'LatDecimal', 'LonDecimal']], use_container_width=True)


