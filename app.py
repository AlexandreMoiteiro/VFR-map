import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster, MiniMap, Fullscreen

# --- ESTILO GLOBAL STREAMLIT ---
st.set_page_config(layout="wide", page_title="VFR Points Map", page_icon="🛩️")
st.markdown("""
<style>
.folium-map {border-radius: 20px; box-shadow: 0 4px 24px #aaa;}
</style>
""", unsafe_allow_html=True)

# --- LER DADOS ---
df = pd.read_csv("significant_places.csv")
df["LatDecimal"] = pd.to_numeric(df["LatDecimal"], errors="coerce")
df["LonDecimal"] = pd.to_numeric(df["LonDecimal"], errors="coerce")
df = df.dropna(subset=["LatDecimal", "LonDecimal"])

# --- TÍTULO E FILTRO NO TOPO ---
st.title("🛩️ Significant VFR Points in Portugal")
st.markdown("Mapa interativo dos principais pontos VFR em Portugal para navegação visual.")
st.write(f"**Total de pontos no mapa:** {len(df)}")

# Filtro de pesquisa central
search = st.text_input("Filtra por nome ou código VFR:", key="filtro_nome")
if search:
    df = df[df['Name'].str.contains(search, case=False) | df['Code'].str.contains(search, case=False)]

# --- PALETA DE CORES BONITA (por prefixo do código) ---
import random
def code_color(code):
    prefix = code[:2]
    color_dict = {
        'AB': '#d7263d', 'AL': '#1b998b', 'AM': '#f46036', 'BA': '#2e294e', 'BE': '#38618c', 'CA': '#e2c044',
        'CO': '#61a5c2', 'EV': '#e84855', 'FA': '#34c759', 'PO': '#495867', 'SE': '#994636', 'VI': '#0d3b66', 'MA': '#00a896'
    }
    return color_dict.get(prefix, "#{:06x}".format(random.randint(0, 0xFFFFFF)))

# --- CRIA MAPA ---
m = folium.Map(
    location=[df["LatDecimal"].mean(), df["LonDecimal"].mean()],
    zoom_start=6.3,
    tiles="CartoDB positron"
)

MiniMap(toggle_display=True).add_to(m)
Fullscreen(position='topright').add_to(m)

marker_cluster = MarkerCluster(name="VFR Points").add_to(m)

for _, row in df.iterrows():
    cor = code_color(row["Code"])
    folium.CircleMarker(
        location=[row["LatDecimal"], row["LonDecimal"]],
        radius=6,
        fill=True,
        color=cor,
        fill_color=cor,
        fill_opacity=0.85,
        weight=2,
        tooltip=folium.Tooltip(
            f"""<b>{row['Name']}</b> <br>
            <small><b>Code:</b> {row['Code']}</small><br>
            <b>Lat:</b> {row['LatDecimal']}<br>
            <b>Lon:</b> {row['LonDecimal']}
            """, sticky=True
        ),
        popup=folium.Popup(f"<b>{row['Name']}</b><br><b>Code:</b> {row['Code']}", max_width=250)
    ).add_to(marker_cluster)

folium.LayerControl().add_to(m)

# --- MOSTRA MAPA ---
st_folium(m, width=1100, height=700)

# --- TABELA DOS PONTOS ---
with st.expander("Ver tabela de pontos VFR"):
    st.dataframe(df[['Name', 'Code', 'LatDecimal', 'LonDecimal']])




