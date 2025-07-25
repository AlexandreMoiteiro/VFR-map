import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster, MiniMap, Fullscreen

# Layout largo e fundo branco
st.set_page_config(page_title="VFR Points Portugal", layout="wide")

# CSS para tirar cor infantil, suavizar tudo
st.markdown("""
    <style>
        body { background-color: #fff !important; }
        .stApp { background-color: #fff; }
        .folium-map { border-radius: 15px; box-shadow: 0 2px 12px #ddd; }
        .stTextInput > div > div > input {font-size: 1.1em;}
        .stDataFrame { border-radius: 15px; }
    </style>
    """, unsafe_allow_html=True)

# ===== Lê e prepara dados =====
df = pd.read_csv("significant_places.csv")
df["LatDecimal"] = pd.to_numeric(df["LatDecimal"], errors="coerce")
df["LonDecimal"] = pd.to_numeric(df["LonDecimal"], errors="coerce")
df = df.dropna(subset=["LatDecimal", "LonDecimal"])

st.title("Significant VFR Points in Portugal")
st.caption("Mapa interativo de pontos de referência VFR. Clica em cada ponto para ver o nome e código.")

col1, col2 = st.columns([3, 1])
with col1:
    search = st.text_input("Filtrar por nome ou código", "")
with col2:
    st.markdown(f"<div style='font-size:18px; margin-top: 18px;'>Total de pontos: <b>{len(df)}</b></div>", unsafe_allow_html=True)

if search:
    df = df[df['Name'].str.contains(search, case=False) | df['Code'].str.contains(search, case=False)]

# ===== Mapa =====
m = folium.Map(
    location=[df["LatDecimal"].mean(), df["LonDecimal"].mean()],
    zoom_start=6.3,
    tiles="CartoDB positron"
)
# Extra: MiniMapa e Fullscreen mas discretos
MiniMap(toggle_display=True).add_to(m)
Fullscreen(position='topright').add_to(m)
marker_cluster = MarkerCluster(name="VFR Points").add_to(m)

for _, row in df.iterrows():
    folium.CircleMarker(
        location=[row["LatDecimal"], row["LonDecimal"]],
        radius=5,
        fill=True,
        color="#2A2A2A",
        fill_color="#404040",
        fill_opacity=0.78,
        weight=1,
        tooltip=f"<b>{row['Name']}</b> ({row['Code']})",
        popup=folium.Popup(f"<b>{row['Name']}</b><br>Código: <b>{row['Code']}</b>", max_width=220)
    ).add_to(marker_cluster)

folium.LayerControl().add_to(m)

# ===== Mostra mapa grande =====
st_folium(m, width=1100, height=680)

# ===== Data Table discreta =====
with st.expander("Ver tabela de pontos VFR"):
    st.dataframe(df[['Name', 'Code', 'LatDecimal', 'LonDecimal']], use_container_width=True)



