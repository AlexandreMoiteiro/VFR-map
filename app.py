import streamlit as st
import pandas as pd
import pydeck as pdk

# --- Lê CSV e prepara dados ---
CSV_PATH = "significant_places.csv"
df = pd.read_csv(CSV_PATH)
df["LatDecimal"] = pd.to_numeric(df["LatDecimal"], errors="coerce")
df["LonDecimal"] = pd.to_numeric(df["LonDecimal"], errors="coerce")
df = df.dropna(subset=["LatDecimal", "LonDecimal"])

# --- Streamlit Layout ---
st.set_page_config(layout="wide")
st.markdown("""
    <style>
        .big-title { font-size: 3em; font-weight: 700; letter-spacing: -2px; }
        .subtitle { font-size: 1.4em; color: #888; margin-bottom: 1.5em;}
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="big-title">VFR Points Portugal</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Mapa interativo dos pontos VFR em Portugal, moderno e responsivo.</div>', unsafe_allow_html=True)

st.write(f"🗺️ **Total de pontos:** {len(df)}")

# --- Filtro Search ---
search = st.text_input("🔎 Filtrar por nome ou código", "")
filtered = df
if search:
    filtered = df[df['Name'].str.contains(search, case=False) | df['Code'].str.contains(search, case=False)]

# --- Layer de Clustering (Hexagon) e Pontos individuais ---
hex_layer = pdk.Layer(
    "HexagonLayer",
    data=filtered,
    get_position='[LonDecimal, LatDecimal]',
    radius=9000,                # (metros, ajusta se quiseres mais clusterização)
    elevation_scale=50,
    elevation_range=[0, 2500],
    pickable=True,
    extruded=True,
    coverage=1,
)

scatter_layer = pdk.Layer(
    "ScatterplotLayer",
    data=filtered,
    get_position='[LonDecimal, LatDecimal]',
    get_color='[32, 169, 226, 180]',  # azul bonito, meio transparente
    get_radius=1700,
    pickable=True,
    auto_highlight=True,
)

# --- Deck.gl Map config com tiles Carto (não precisa token) ---
MAP_STYLE = "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json"

view = pdk.ViewState(
    latitude=filtered["LatDecimal"].mean(),
    longitude=filtered["LonDecimal"].mean(),
    zoom=6.4 if len(filtered) > 1 else 10,
    pitch=36,    # ligeiro 3D, podes pôr 0 para flat
    bearing=2
)

tooltip = {
    "html": "<b>{Name}</b> <span style='color:#888'>({Code})</span><br>"
            "Lat: <b>{LatDecimal:.4f}</b><br>"
            "Lon: <b>{LonDecimal:.4f}</b>",
    "style": {
        "backgroundColor": "#fff",
        "color": "#333",
        "fontSize": "1.1em",
        "borderRadius": "8px",
        "padding": "10px"
    }
}

r = pdk.Deck(
    map_style=MAP_STYLE,
    initial_view_state=view,
    layers=[hex_layer, scatter_layer],
    tooltip=tooltip,
)

# --- Render Mapa Pydeck ---
st.pydeck_chart(r, use_container_width=True)

# --- Data Table, opcional ---
with st.expander("👁️ Ver tabela de dados"):
    st.dataframe(filtered[['Name', 'Code', 'LatDecimal', 'LonDecimal']])




