import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="VFR Points Portugal", layout="wide")

# CSS para centralizar e dar aspeto clean
st.markdown("""
    <style>
        .stApp { background-color: #fafbfc; }
        .folium-map { border-radius: 16px; box-shadow: 0 2px 16px #e2e2e2; }
        .stTextInput > div > div > input {font-size: 1.14em; text-align: center;}
        .stDataFrame { border-radius: 15px; }
    </style>
""", unsafe_allow_html=True)

df = pd.read_csv("significant_places.csv")
df["LatDecimal"] = pd.to_numeric(df["LatDecimal"], errors="coerce")
df["LonDecimal"] = pd.to_numeric(df["LonDecimal"], errors="coerce")
df = df.dropna(subset=["LatDecimal", "LonDecimal"])

# Título centralizado
st.markdown(
    "<h1 style='text-align:center; font-weight:600; letter-spacing:-1px;'>Significant VFR Points - Portugal</h1>",
    unsafe_allow_html=True,
)

# ==== Seleção de mapa de fundo e filtro ====
cols = st.columns([2, 5, 2])
with cols[1]:
    map_tile = st.selectbox(
        "Tipo de mapa de fundo",
        [
            "CartoDB Positron (Claro)",
            "CartoDB Dark (Noite)",
            "Esri Satélite (Híbrido)"
        ],
        index=0
    )
    search = st.text_input("Filtrar por nome ou código VFR", "")

if search:
    df = df[df["Name"].str.contains(search, case=False) | df["Code"].str.contains(search, case=False)]

# Info total centralizado
st.markdown(
    f"<div style='text-align:center; font-size:17px; color:#888; margin-bottom:10px;'>Pontos visíveis: <b>{len(df)}</b></div>",
    unsafe_allow_html=True,
)

# Centro fixo (continente) — nunca muda!
CENTER_PT = [39.7, -8.1]

# --- Cria o mapa base ---
if map_tile == "CartoDB Positron (Claro)":
    m = folium.Map(
        location=CENTER_PT,
        zoom_start=7,
        tiles="CartoDB positron",
        control_scale=True
    )
elif map_tile == "CartoDB Dark (Noite)":
    m = folium.Map(
        location=CENTER_PT,
        zoom_start=7,
        tiles="CartoDB dark_matter",
        control_scale=True
    )
elif map_tile == "Esri Satélite (Híbrido)":
    m = folium.Map(
        location=CENTER_PT,
        zoom_start=7,
        tiles=None,  # Sem base default!
        control_scale=True
    )
    # Satélite ESRI
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        name="Esri Satellite",
        overlay=False,
        control=False
    ).add_to(m)
    # Labels Esri (simula “híbrido”)
    folium.TileLayer(
        tiles="https://services.arcgisonline.com/arcgis/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}",
        attr="Esri Labels",
        name="Labels",
        overlay=True,
        control=False
    ).add_to(m)

POINT_COLOR = "#194569"  # Azul escuro discreto

for _, row in df.iterrows():
    folium.CircleMarker(
        location=[row["LatDecimal"], row["LonDecimal"]],
        radius=5.5,
        fill=True,
        color=POINT_COLOR,
        fill_color=POINT_COLOR,
        fill_opacity=0.78,
        weight=1,
        tooltip=f"{row['Name']} ({row['Code']})",
        popup=folium.Popup(f"<b>{row['Name']}</b><br>Código: <b>{row['Code']}</b>", max_width=210)
    ).add_to(m)

# Centraliza o mapa visualmente na página
map_cols = st.columns([0.1, 0.8, 0.1])
with map_cols[1]:
    st_folium(m, width=1100, height=650)

with st.expander("Ver tabela dos pontos visíveis"):
    st.dataframe(df[["Name", "Code", "LatDecimal", "LonDecimal"]], use_container_width=True)

