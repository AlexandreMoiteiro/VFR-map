import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="VFR Points Portugal", layout="wide")

# -- CSS para centrar o mapa
st.markdown("""
    <style>
        .centered-map {
            display: flex;
            justify-content: center;
            align-items: center;
            margin-bottom: 0.5em;
            width: 100%;
        }
        .folium-map {
            border-radius: 16px;
            box-shadow: 0 2px 20px #e0e0e0;
        }
    </style>
""", unsafe_allow_html=True)

# -- Dados
df = pd.read_csv("significant_places.csv")
df["LatDecimal"] = pd.to_numeric(df["LatDecimal"], errors="coerce")
df["LonDecimal"] = pd.to_numeric(df["LonDecimal"], errors="coerce")
df = df.dropna(subset=["LatDecimal", "LonDecimal"])

# -- Títulos
st.markdown('<h1 style="text-align:center;">Significant VFR Points in Portugal</h1>', unsafe_allow_html=True)
st.markdown('<div style="text-align:center; color:#6e6e6e; margin-bottom: 1.3em;">Mapa interativo profissional dos pontos VFR nacionais</div>', unsafe_allow_html=True)
st.markdown('<div style="text-align:center; margin-bottom: 0.7em;">', unsafe_allow_html=True)
search = st.text_input("Filtrar por nome ou código VFR", "", key="filtro", label_visibility="collapsed", help="Pesquisar por nome ou código VFR")
st.markdown('</div>', unsafe_allow_html=True)
st.markdown(f"<div style='text-align:center; font-size:17px; margin-bottom:10px;'>Total de pontos: <b>{len(df)}</b></div>", unsafe_allow_html=True)

if search:
    df = df[df['Name'].str.contains(search, case=False) | df['Code'].str.contains(search, case=False)]

# -- Cria mapa (centrado em Portugal Continental)
map_center = [39.6, -8.2]
m = folium.Map(location=map_center, zoom_start=7, tiles="CartoDB positron")

for _, row in df.iterrows():
    folium.CircleMarker(
        location=[row["LatDecimal"], row["LonDecimal"]],
        radius=6,
        color="#fff",             # contorno branco
        fill_color="#1a237e",     # azul escuro
        fill_opacity=0.82,
        weight=1.2,
        tooltip=f"<b>{row['Name']}</b> <span style='color:#9e9e9e;'>({row['Code']})</span>",
        popup=folium.Popup(f"<b>{row['Name']}</b><br>Código: <b>{row['Code']}</b>", max_width=230)
    ).add_to(m)

# -- Container que centra o mapa na página
st.markdown('<div class="centered-map">', unsafe_allow_html=True)
st_folium(m, width=900, height=600)
st.markdown('</div>', unsafe_allow_html=True)

with st.expander("Ver tabela de pontos visíveis"):
    st.dataframe(df[['Name', 'Code', 'LatDecimal', 'LonDecimal']], use_container_width=True)



