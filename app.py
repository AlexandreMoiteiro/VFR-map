import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster, LocateControl, Search
from streamlit_folium import st_folium

st.set_page_config(page_title="VFR Map Portugal", layout="wide")

# Lê o ficheiro CSV
CSV_PATH = "significant_places.csv"
df = pd.read_csv(CSV_PATH)
df["LatDecimal"] = pd.to_numeric(df["LatDecimal"], errors="coerce")
df["LonDecimal"] = pd.to_numeric(df["LonDecimal"], errors="coerce")
df = df.dropna(subset=["LatDecimal", "LonDecimal"])

# Filtro pesquisa
search = st.text_input("🔍 Pesquisa ponto por nome ou código", "")
if search:
    df = df[df['Name'].str.contains(search, case=False) | df['Code'].str.contains(search, case=False)]

st.title("🛩️ Significant VFR Points in Portugal")
st.markdown(
    "Mapa interativo de pontos VFR para navegação visual. Usa o filtro acima para procurar um ponto ou clica sobre qualquer marcador para detalhes. Arrasta, faz zoom, e troca o fundo do mapa à vontade."
)
st.write(f"**Total de pontos no mapa:** {len(df)}")

with st.expander("📋 Ver tabela de pontos"):
    st.dataframe(df[['Name', 'Code', 'LatDecimal', 'LonDecimal']])

# Centro do mapa em Portugal
mean_lat = df["LatDecimal"].mean()
mean_lon = df["LonDecimal"].mean()
m = folium.Map(location=[mean_lat, mean_lon], zoom_start=6, tiles=None)

# Camadas de mapa bonitas
folium.TileLayer("OpenStreetMap", name="Streets").add_to(m)
folium.TileLayer("CartoDB positron", name="Light").add_to(m)
folium.TileLayer("Stamen Terrain", name="Terrain").add_to(m)
folium.TileLayer("Stamen Toner", name="Toner").add_to(m)
folium.TileLayer("Esri Satellite", name="Satellite",
    tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attr="Esri"
).add_to(m)

# Adiciona cluster de marcadores
marker_cluster = MarkerCluster(name="Pontos VFR").add_to(m)

for _, row in df.iterrows():
    folium.CircleMarker(
        location=[row["LatDecimal"], row["LonDecimal"]],
        radius=6,
        color="#2066e0",
        fill=True,
        fill_color="#ff7700",
        fill_opacity=0.85,
        weight=2,
        tooltip=folium.Tooltip(f"<b>{row['Name']}</b> ({row['Code']})"),
        popup=folium.Popup(f"""
            <div style='font-family:monospace;font-size:14px;'>
                <b>{row['Name']}</b><br>
                Código: <b>{row['Code']}</b><br>
                Latitude: {row['LatDecimal']}<br>
                Longitude: {row['LonDecimal']}
            </div>
        """, max_width=250)
    ).add_to(marker_cluster)

# Botão para localizar o utilizador
LocateControl(auto_start=False, flyTo=True, strings={"title": "Onde estou?"}).add_to(m)

# Permite pesquisar por código diretamente no mapa (não precisa de reload)
search_layer = Search(
    layer=marker_cluster,
    search_label="tooltip",
    placeholder="Procurar no mapa...",
    collapsed=True
).add_to(m)

# Layer control
folium.LayerControl().add_to(m)

# Mostra o mapa bonito no Streamlit
st_folium(m, width=1050, height=700, returned_objects=[])







