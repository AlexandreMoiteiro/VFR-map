import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# ==== HIDE STREAMLIT DEFAULT STUFF (sidebar, footer, etc) ====
hide_streamlit_style = """
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .css-1kyxreq {padding-top: 2rem;}
        .block-container {padding-top: 2rem;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# ==== PAGE SETUP ====
st.set_page_config(page_title="VFR Points Portugal", layout="wide", page_icon="✈️")

# ==== DATA ====
CSV_PATH = "significant_places.csv"
df = pd.read_csv(CSV_PATH)
df["LatDecimal"] = pd.to_numeric(df["LatDecimal"], errors="coerce")
df["LonDecimal"] = pd.to_numeric(df["LonDecimal"], errors="coerce")
df = df.dropna(subset=["LatDecimal", "LonDecimal"])

# ==== TITLE / SEARCH ====
st.markdown("<h1 style='text-align: center; margin-bottom:0.1em;'>Significant VFR Points Portugal</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #888; margin-bottom:2em;'>Visual reporting points for VFR navigation</p>", unsafe_allow_html=True)

# Barra de pesquisa simples e discreta
search = st.text_input("", placeholder="Search by name or code...", key="search_input")
if search:
    df = df[df["Name"].str.contains(search, case=False) | df["Code"].str.contains(search, case=False)]

st.markdown(f"<p style='text-align: center; color:#444; font-size:1.1em;'>Total points: <b>{len(df)}</b></p>", unsafe_allow_html=True)

# ==== FOLIUM MAP ====
m = folium.Map(
    location=[df["LatDecimal"].mean(), df["LonDecimal"].mean()],
    zoom_start=6,
    tiles="CartoDB positron",  # Mapa mais clean/minimal
    control_scale=True,
    prefer_canvas=True
)

# CLUSTER para ficar clean quando muitos pontos (podes tirar se quiseres tudo visível sempre)
from folium.plugins import MarkerCluster
cluster = MarkerCluster(showCoverageOnHover=False, spiderfyOnMaxZoom=True, disableClusteringAtZoom=10).add_to(m)

for _, row in df.iterrows():
    folium.CircleMarker(
        location=[row["LatDecimal"], row["LonDecimal"]],
        radius=5,
        fill=True,
        color="#1976d2",  # azul-profissional
        fill_color="#1976d2",
        fill_opacity=0.80,
        weight=0,
        tooltip=folium.Tooltip(
            f"<b>{row['Name']}</b><br><span style='color:#1976d2;'>Code: {row['Code']}</span><br>"
            f"Lat: {row['LatDecimal']:.5f}<br>Lon: {row['LonDecimal']:.5f}",
            sticky=True,
            direction='top'
        ),
    ).add_to(cluster)

st_folium(m, width=1000, height=650)

# (Opcional) tabela expansível minimalista
with st.expander("Show table", expanded=False):
    st.dataframe(df[["Name", "Code", "LatDecimal", "LonDecimal"]], hide_index=True, use_container_width=True)









