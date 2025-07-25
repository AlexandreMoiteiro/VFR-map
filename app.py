import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

# === SIDEBAR / CONFIG ===
st.set_page_config(page_title="VFR Points Portugal", layout="wide")
st.sidebar.title("🔎 Filtros")
st.title("🗺️ Significant VFR Points in Portugal")
st.caption("Mapa interativo de pontos de navegação VFR em Portugal, com cluster, pesquisa e visual moderno.")

# === LOAD DATA ===
CSV_PATH = "significant_places.csv"
df = pd.read_csv(CSV_PATH)
df["LatDecimal"] = pd.to_numeric(df["LatDecimal"], errors="coerce")
df["LonDecimal"] = pd.to_numeric(df["LonDecimal"], errors="coerce")
df = df.dropna(subset=["LatDecimal", "LonDecimal"])

# === FILTERS ===
search = st.sidebar.text_input("Filtrar por Nome ou Código").strip()
if search:
    df = df[df['Name'].str.contains(search, case=False) | df['Code'].str.contains(search, case=False)]

# (Extra) Filtro por prefixo do código
prefix = st.sidebar.text_input("Começa por código (opcional)").strip().upper()
if prefix:
    df = df[df['Code'].str.startswith(prefix)]

st.sidebar.markdown(f"**{len(df)} pontos visíveis**")

# === DATA TABLE (TOGGLE) ===
with st.expander("🗂️ Ver tabela de dados"):
    st.dataframe(df[['Name', 'Code', 'LatDecimal', 'LonDecimal']], use_container_width=True)

# === MAP SETUP ===
# Mapa escuro bonito, zoom centrado
map_center = [df["LatDecimal"].mean(), df["LonDecimal"].mean()]
m = folium.Map(
    location=map_center,
    zoom_start=6.3,
    tiles="CartoDB dark_matter"
)

# CLUSTER (com popups bonitos)
marker_cluster = MarkerCluster().add_to(m)

for _, row in df.iterrows():
    popup_html = f"""
        <div style='font-family:Montserrat,Arial;font-size:14px;'>
            <b>{row['Name']}</b> <br>
            <b>Code:</b> <span style='color:#f44336;'>{row['Code']}</span><br>
            <b>Lat:</b> {row['LatDecimal']:.5f}<br>
            <b>Lon:</b> {row['LonDecimal']:.5f}
        </div>
    """
    folium.CircleMarker(
        location=[row["LatDecimal"], row["LonDecimal"]],
        radius=6,
        fill=True,
        color="#2196F3",  # azul bonito
        fill_color="#00e0ff",
        fill_opacity=0.85,
        popup=folium.Popup(popup_html, max_width=250, min_width=150),
        tooltip=row['Code'],
        weight=2
    ).add_to(marker_cluster)

# MAPA RESPONSIVO
st_data = st_folium(m, use_container_width=True, height=700, returned_objects=[])

st.markdown("""
<style>
    /* Melhora tooltips no dark map */
    .leaflet-popup-content-wrapper, .leaflet-popup-tip {
        background: #1c2024 !important;
        color: #f5f5f5 !important;
        font-family: 'Montserrat', Arial, sans-serif;
        font-size: 14px;
    }
</style>
""", unsafe_allow_html=True)








