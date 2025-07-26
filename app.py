import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# Config layout
st.set_page_config(page_title="VFR Points Portugal", layout="wide")

# CSS minimalista
st.markdown("""
    <style>
    .stApp { background: #f7f7f7; }
    .folium-map { border-radius: 12px; margin: 0 auto; box-shadow: 0 4px 18px #e1e1e1;}
    h1 { text-align: center !important; }
    </style>
""", unsafe_allow_html=True)

# Carrega dados
df = pd.read_csv("significant_places.csv")
df["LatDecimal"] = pd.to_numeric(df["LatDecimal"], errors="coerce")
df["LonDecimal"] = pd.to_numeric(df["LonDecimal"], errors="coerce")
df = df.dropna(subset=["LatDecimal", "LonDecimal"])

# Título e filtro centralizado
st.markdown("<h1 style='text-align:center;'>Significant VFR Points in Portugal</h1>", unsafe_allow_html=True)
st.markdown("<div style='text-align:center; color:#444; font-size:1.08em; margin-bottom:18px;'>Mapa interativo — clique nos pontos para detalhes</div>", unsafe_allow_html=True)

# Campo de pesquisa, centrado
cols = st.columns([2, 4, 2])
with cols[1]:
    search = st.text_input("Filtrar por nome ou código VFR", "")

if search:
    df = df[df['Name'].str.contains(search, case=False) | df['Code'].str.contains(search, case=False)]

# Total visível, centralizado
st.markdown(f"<div style='text-align:center; font-size:17px; margin-bottom: 9px;'>Pontos visíveis: <b>{len(df)}</b></div>", unsafe_allow_html=True)

# Centro fixo de Portugal Continental (Arouca/Coimbra área, NÃO média dos dados)
center_lat, center_lon = 39.7, -8.1

m = folium.Map(
    location=[center_lat, center_lon],
    zoom_start=7,
    tiles="CartoDB Positron",
    control_scale=True
)

# Pontos com aspeto profissional: azul petróleo ou laranja sóbrio
POINT_COLOR = "#205081"  # Azul petróleo (ou "#EA7317" para laranja elegante)
for _, row in df.iterrows():
    folium.CircleMarker(
        location=[row["LatDecimal"], row["LonDecimal"]],
        radius=5.5,
        fill=True,
        color="white",
        fill_color=POINT_COLOR,
        fill_opacity=0.92,
        weight=1,
        tooltip=f"{row['Name']} ({row['Code']})",
        popup=folium.Popup(
            f"<b>{row['Name']}</b><br>Código: <b>{row['Code']}</b>", max_width=220
        )
    ).add_to(m)

# Remove clusters: só marcadores individuais
# Fullscreen e minimap removidos para ainda mais clean

# Mapa super largo, sempre central, sem barras
st_folium(m, width=1200, height=640, use_container_width=False)

# Tabela só se quiseres (opcional)
with st.expander("Ver tabela dos pontos mostrados no mapa"):
    st.dataframe(df[['Name', 'Code', 'LatDecimal', 'LonDecimal']], use_container_width=True)



