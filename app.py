import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster, Search
from streamlit_folium import st_folium

# === Estética do Streamlit ===
st.set_page_config(page_title="VFR Points Portugal", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    .css-1kyxreq { background: #f8fafc !important; }
    .folium-map { border-radius: 16px; box-shadow: 0 4px 16px #0002; }
    </style>
""", unsafe_allow_html=True)

# === Leitura e limpeza dos dados ===
df = pd.read_csv("significant_places.csv")
df["LatDecimal"] = pd.to_numeric(df["LatDecimal"], errors="coerce")
df["LonDecimal"] = pd.to_numeric(df["LonDecimal"], errors="coerce")
df = df.dropna(subset=["LatDecimal", "LonDecimal"])

# === Filtro de pesquisa ===
col1, col2 = st.columns([2,1])
with col1:
    st.title("🗺️ Pontos VFR Significativos - Portugal")
    st.write(
        "Mapa interativo de pontos VFR (Visual Reporting Points) para navegação visual. "
        "Aproxime, clique nos marcadores para mais detalhes ou utilize a caixa de pesquisa."
    )
with col2:
    search = st.text_input("🔍 Pesquisar por nome ou código", "")

if search:
    df = df[df['Name'].str.contains(search, case=False) | df['Code'].str.contains(search, case=False)]

st.write(f"**Total de pontos no mapa:** {len(df)}")

# === Criação do mapa ===
m = folium.Map(
    location=[df["LatDecimal"].mean(), df["LonDecimal"].mean()],
    zoom_start=6.3,
    tiles="CartoDB Positron"
)

# Cluster para agrupar pontos próximos
marker_cluster = MarkerCluster(
    name="VFR Points",
    disableClusteringAtZoom=10
).add_to(m)

# Lista para pesquisa no mapa
search_data = []

# Marcação dos pontos
for _, row in df.iterrows():
    popup_html = f"""
        <div style='font-size:16px; font-weight:600'>{row['Name']} <span style='font-size:12px;'>({row['Code']})</span></div>
        <div style='font-size:13px;'>Latitude: <b>{row['LatDecimal']}</b><br>
        Longitude: <b>{row['LonDecimal']}</b></div>
    """
    marker = folium.Marker(
        location=[row["LatDecimal"], row["LonDecimal"]],
        popup=folium.Popup(popup_html, max_width=300),
        icon=folium.Icon(color="red", icon="glyphicon glyphicon-flag"),
        tooltip=f"{row['Name']} ({row['Code']})"
    )
    marker.add_to(marker_cluster)
    # Para a busca
    search_data.append({
        "loc": [row["LatDecimal"], row["LonDecimal"]],
        "title": f"{row['Name']} ({row['Code']})"
    })

# Search no mapa
Search(
    layer=marker_cluster,
    search_label="title",
    placeholder="Pesquisar ponto no mapa...",
    collapsed=False
).add_to(m)

# Layer control
folium.LayerControl().add_to(m)

# Mostra o mapa bonitão
st_folium(m, width=950, height=650)

# Opcional: Tabela dos dados
with st.expander("Mostrar tabela de pontos VFR"):
    st.dataframe(df[['Name', 'Code', 'LatDecimal', 'LonDecimal']])

st.info("Dica: Use o zoom e a pesquisa para localizar rapidamente um ponto específico. Pode clicar nos marcadores para detalhes.")






