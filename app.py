import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="VFR Points Portugal", layout="wide")

# CSS: centra tudo, limpa fundo, remove margens default, mapa grande e centrado
st.markdown("""
<style>
    .stApp { background-color: #fff; }
    #MainMenu, header, footer {visibility: hidden;}
    .block-container {padding-top: 20px; max-width: 100vw;}
    .main-title {text-align: center; font-size: 2.3em; margin-bottom: 0.2em; color: #222; letter-spacing: 0.01em;}
    .main-desc {text-align: center; color: #6e6e6e; margin-bottom: 1.2em;}
    .filterbox {display: flex; justify-content: center; margin-bottom: 0.4em;}
    .folium-map {margin: 0 auto !important; border-radius: 16px; box-shadow: 0 2px 20px #e0e0e0;}
</style>
""", unsafe_allow_html=True)

# Dados
df = pd.read_csv("significant_places.csv")
df["LatDecimal"] = pd.to_numeric(df["LatDecimal"], errors="coerce")
df["LonDecimal"] = pd.to_numeric(df["LonDecimal"], errors="coerce")
df = df.dropna(subset=["LatDecimal", "LonDecimal"])

# Título e descrição centrados
st.markdown('<div class="main-title">Significant VFR Points in Portugal</div>', unsafe_allow_html=True)
st.markdown('<div class="main-desc">Mapa interativo profissional dos pontos VFR nacionais. Sóbrio, centrado e minimalista.</div>', unsafe_allow_html=True)

# Filtro, perfeitamente centrado
st.markdown('<div class="filterbox">', unsafe_allow_html=True)
search = st.text_input("Filtrar por nome ou código VFR", "", key="filtro", label_visibility="collapsed", help="Pesquisar por nome ou código VFR")
st.markdown('</div>', unsafe_allow_html=True)

if search:
    df = df[df['Name'].str.contains(search, case=False) | df['Code'].str.contains(search, case=False)]

# Texto total central
st.markdown(f"<div style='text-align:center; font-size:17px; margin-bottom:12px;'>Total de pontos: <b>{len(df)}</b></div>", unsafe_allow_html=True)

# Mapa: centrado no continente, aspeto neutro, pontos azul escuro, sem clusters
center_portugal = [39.6, -8.2]
m = folium.Map(location=center_portugal, zoom_start=7, tiles="CartoDB positron")

# Personalização dos pontos (Azul escuro, contorno branco subtil, moderno)
for _, row in df.iterrows():
    folium.CircleMarker(
        location=[row["LatDecimal"], row["LonDecimal"]],
        radius=6,
        color="#fff",             # contorno branco discreto
        fill_color="#214E8F",     # azul escuro sóbrio (troca para #FF9900 para laranja ou #222 para cinza)
        fill_opacity=0.85,
        weight=1.2,
        tooltip=f"<b>{row['Name']}</b> <span style='color:#9e9e9e;'>({row['Code']})</span>",
        popup=folium.Popup(f"<b>{row['Name']}</b><br>Código: <b>{row['Code']}</b>", max_width=230)
    ).add_to(m)

# Mapa ultra-central, 1000px largo, no centro da página
st_folium(m, width=1000, height=630)

# Tabela em expander
with st.expander("Ver tabela de pontos visíveis"):
    st.dataframe(df[['Name', 'Code', 'LatDecimal', 'LonDecimal']], use_container_width=True)



