import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster, MiniMap, Fullscreen

st.set_page_config(layout="wide")

st.markdown(
    """
    <style>
    .main {background-color: #f5f6fa;}
    .folium-map {border-radius: 18px; box-shadow: 0 2px 18px #ccc;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ===== 1. Lê e prepara dados =====
df = pd.read_csv("significant_places.csv")
df["LatDecimal"] = pd.to_numeric(df["LatDecimal"], errors="coerce")
df["LonDecimal"] = pd.to_numeric(df["LonDecimal"], errors="coerce")
df = df.dropna(subset=["LatDecimal", "LonDecimal"])

# ===== 2. Barra lateral com filtros =====
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/189/189672.png", width=70)
    st.title("Filtros")
    search = st.text_input("Nome ou Código VFR")
    color_by_code = st.checkbox("Colorir por prefixo do código", value=True)
    st.markdown("---")
    st.caption("Powered by [Streamlit](https://streamlit.io/) + [Folium](https://python-visualization.github.io/folium/)")

if search:
    df = df[df['Name'].str.contains(search, case=False) | df['Code'].str.contains(search, case=False)]

st.title("🛩️ Significant VFR Points in Portugal")
st.write(f"**Total de pontos no mapa:** {len(df)}")

# ===== 3. Função para cor personalizada =====
import random

def code_color(code):
    # Customiza por prefixo ou random só para exemplo
    prefix = code[:2]
    color_dict = {
        'AB': '#D7263D', 'AL': '#8B5E83', 'BA': '#254441', 'BE': '#0597F2', 
        'CA': '#9BC53D', 'CO': '#FFA400', 'EV': '#D7263D', 'FA': '#6A0572',
        'PO': '#3B1F2B', 'SE': '#0A1128', 'VI': '#660708', 'MA': '#007566'
    }
    return color_dict.get(prefix, "#{:06x}".format(random.randint(0, 0xFFFFFF)))

# ===== 4. Cria o mapa bonito =====
m = folium.Map(
    location=[df["LatDecimal"].mean(), df["LonDecimal"].mean()],
    zoom_start=6.3,
    tiles="CartoDB positron"
)

# Extra: MiniMap, FullScreen
MiniMap(toggle_display=True).add_to(m)
Fullscreen(position='topright').add_to(m)

# Cluster para evitar poluição visual
marker_cluster = MarkerCluster(name="VFR Points").add_to(m)

for _, row in df.iterrows():
    if color_by_code:
        marker_color = code_color(row["Code"])
    else:
        marker_color = "red"
    folium.CircleMarker(
        location=[row["LatDecimal"], row["LonDecimal"]],
        radius=6,
        fill=True,
        color=marker_color,
        fill_color=marker_color,
        fill_opacity=0.85,
        weight=2,
        tooltip=folium.Tooltip(
            f"""
            <b>{row['Name']}</b> <br>
            <small><b>Code:</b> {row['Code']}</small><br>
            <b>Lat:</b> {row['LatDecimal']}<br>
            <b>Lon:</b> {row['LonDecimal']}
            """, sticky=True
        ),
        popup=folium.Popup(f"<b>{row['Name']}</b><br><b>Code:</b> {row['Code']}", max_width=250)
    ).add_to(marker_cluster)

folium.LayerControl().add_to(m)

# ===== 5. Mostra mapa responsivo =====
st_folium(m, width=1100, height=700, returned_objects=[])

# ===== 6. Data Table abaixo =====
with st.expander("Ver tabela de pontos VFR"):
    st.dataframe(df[['Name', 'Code', 'LatDecimal', 'LonDecimal']])


