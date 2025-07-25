import streamlit as st
import pandas as pd
import leafmap.foliumap as leafmap

# 1. Layout global e título
st.set_page_config(layout="wide", page_title="VFR Points Portugal", page_icon="🛩️")
st.markdown("""
<style>
.folium-map {
    border-radius: 18px;
    box-shadow: 0 4px 32px #bbb;
    margin-bottom: 30px;
}
.dataframe {
    border-radius: 14px;
    box-shadow: 0 2px 10px #ddd;
}
</style>
""", unsafe_allow_html=True)

st.title("🛩️ Significant VFR Points in Portugal")
st.caption("Mapa profissional e interativo dos principais pontos VFR para navegação visual.")

# 2. Lê e prepara dados
df = pd.read_csv("significant_places.csv")
df["LatDecimal"] = pd.to_numeric(df["LatDecimal"], errors="coerce")
df["LonDecimal"] = pd.to_numeric(df["LonDecimal"], errors="coerce")
df = df.dropna(subset=["LatDecimal", "LonDecimal"])

# 3. Filtro clean no topo
col1, col2 = st.columns([1.5,1])
with col1:
    search = st.text_input("🔍 Filtra por nome ou código VFR:", key="filtro_nome", help="Procura por parte do nome ou código VFR.")
with col2:
    show_table = st.checkbox("Mostrar tabela", value=False)

if search:
    df = df[df['Name'].str.contains(search, case=False) | df['Code'].str.contains(search, case=False)]

# 4. Geração de cor "clean" por prefixo de código (para clusters)
import random
def code_color(code):
    prefix = code[:2].upper()
    color_dict = {
        'AB': '#d7263d', 'AL': '#1b998b', 'AM': '#f46036', 'BA': '#2e294e', 'BE': '#38618c', 'CA': '#e2c044',
        'CO': '#61a5c2', 'EV': '#e84855', 'FA': '#34c759', 'PO': '#495867', 'SE': '#994636', 'VI': '#0d3b66', 'MA': '#00a896'
    }
    return color_dict.get(prefix, "#{:06x}".format(random.randint(0, 0xFFFFFF)))

df["Color"] = df["Code"].apply(code_color)

# 5. Cria mapa leafmap (visual clean, topo, pro)
m = leafmap.Map(
    center=[df["LatDecimal"].mean(), df["LonDecimal"].mean()],
    zoom=6.3,
    tiles="CartoDB.Positron", # visual limpo e moderno
    draw_control=False,
    measure_control=True,
    minimap_control=True,
    fullscreen_control=True,
    attribution_control=False,
    locate_control=True,
)

# 6. Adiciona clusters e tooltips/popups bonitos
# Cluster com cor custom, tooltip clean
geojson_list = []
for _, row in df.iterrows():
    geojson_list.append({
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [row["LonDecimal"], row["LatDecimal"]]},
        "properties": {
            "Name": row["Name"],
            "Code": row["Code"],
            "Lat": round(row["LatDecimal"], 5),
            "Lon": round(row["LonDecimal"], 5),
            "Color": row["Color"],
            "popup": f"""
                <div style='font-size:15px;line-height:1.6'>
                    <b>{row['Name']}</b><br>
                    <span style='font-size:12px;color:#888'>Code:</span> <b>{row['Code']}</b><br>
                    <span style='font-size:12px'>Lat:</span> {row['LatDecimal']:.5f}<br>
                    <span style='font-size:12px'>Lon:</span> {row['LonDecimal']:.5f}
                </div>
            """,
        }
    })

m.add_geojson(
    {
        "type": "FeatureCollection",
        "features": geojson_list,
    },
    layer_name="VFR Points",
    info_mode="on_hover",  # mostra tooltip ao passar o rato
    marker_type="circle-marker",
    marker_kwargs={
        "radius": 7,
        "fillOpacity": 0.92,
        "weight": 2,
        "color": None,  # edge
        "fillColor": "properties.Color",
        "popup": "properties.popup"
    },
    clustering=True
)

# 7. Mostra o mapa
st.markdown("### Mapa Interativo")
m.to_streamlit(height=710)

# 8. Tabela clean e responsiva (opcional)
if show_table:
    st.markdown("### Tabela dos pontos VFR")
    st.dataframe(
        df[['Name', 'Code', 'LatDecimal', 'LonDecimal']],
        use_container_width=True,
        hide_index=True
    )

st.caption("Visualização: tiles CartoDB Positron · Cores distintas por prefixo VFR · Cluster automático · Medição de distâncias · Fullscreen · Minimap")








