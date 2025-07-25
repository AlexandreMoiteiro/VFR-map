import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# Configuração clean
st.set_page_config(page_title="VFR Points Portugal", layout="wide")
st.markdown("""
    <style>
        .stApp { background-color: #fbfbfb; }
        .folium-map { border-radius: 14px; box-shadow: 0 2px 14px #e2e2e2; margin: 0 auto; }
        .stTextInput > div > div > input {font-size: 1.1em;}
        .stDataFrame { border-radius: 14px; }
        .block-container { padding-top: 2rem; }
    </style>
""", unsafe_allow_html=True)

# Ler dados
df = pd.read_csv("significant_places.csv")
df["LatDecimal"] = pd.to_numeric(df["LatDecimal"], errors="coerce")
df["LonDecimal"] = pd.to_numeric(df["LonDecimal"], errors="coerce")
df = df.dropna(subset=["LatDecimal", "LonDecimal"])

# Filtro no topo
st.markdown("<h1 style='text-align:center; font-size:2.4em;'>Significant VFR Points in Portugal</h1>", unsafe_allow_html=True)
st.markdown("<div style='text-align:center; color:#555; font-size:1.13em;'>Mapa interativo e minimalista dos pontos VFR nacionais</div>", unsafe_allow_html=True)

colf = st.columns([3, 2, 3])
with colf[1]:
    search = st.text_input("🔎 Filtrar por nome ou código VFR", "")

if search:
    df = df[df['Name'].str.contains(search, case=False) | df['Code'].str.contains(search, case=False)]

st.markdown(f"<div style='text-align:center; font-size:18px; margin-bottom: 12px;'>Total de pontos visíveis: <b>{len(df)}</b></div>", unsafe_allow_html=True)

# Mapa centrado mesmo no centro geográfico de Portugal continental (latitude, longitude exata)
map_center = [39.5, -8.0]  # centro de Portugal continental
m = folium.Map(
    location=map_center,
    zoom_start=7,
    tiles="CartoDB positron"
)

# Pontos modernos (azul escuro, ou troca por laranja elegante se preferires)
point_color = "#1864ab"   # Azul escuro (ou "#ff9900" para laranja soft)
for _, row in df.iterrows():
    folium.CircleMarker(
        location=[row["LatDecimal"], row["LonDecimal"]],
        radius=5.5,
        fill=True,
        color=point_color,
        fill_color=point_color,
        fill_opacity=0.82,
        weight=0.5,
        tooltip=f"<b>{row['Name']}</b> ({row['Code']})",
        popup=folium.Popup(f"<b>{row['Name']}</b><br>Código: <b>{row['Code']}</b>", max_width=210)
    ).add_to(m)

# Remove clusters para ser mais limpo (adiciona se preferires para >300 pontos)
st_folium(m, width=950, height=600)

with st.expander("Ver tabela dos pontos visíveis"):
    st.dataframe(df[['Name', 'Code', 'LatDecimal', 'LonDecimal']], use_container_width=True)




