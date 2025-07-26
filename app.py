import streamlit as st
import pandas as pd
from keplergl import KeplerGl
from streamlit_keplergl import keplergl_static

CSV_PATH = "significant_places.csv"
df = pd.read_csv(CSV_PATH)

# Limpeza das coordenadas
df["LatDecimal"] = pd.to_numeric(df["LatDecimal"], errors="coerce")
df["LonDecimal"] = pd.to_numeric(df["LonDecimal"], errors="coerce")
df = df.dropna(subset=["LatDecimal", "LonDecimal"])

# Filtro
search = st.text_input("Filtra por nome ou código", "")
filtered = df
if search:
    filtered = df[df['Name'].str.contains(search, case=False) | df['Code'].str.contains(search, case=False)]

st.title("Significant VFR Points in Portugal (Kepler.gl)")
st.write(f"Total de pontos no mapa: {len(filtered)}")

with st.expander("Show Data Table"):
    st.dataframe(filtered[['Name', 'Code', 'LatDecimal', 'LonDecimal']])

# Cria um mapa Kepler
map_1 = KeplerGl(height=600)
map_1.add_data(data=filtered, name="VFR Points")

# Exibe no Streamlit (static, mas totalmente navegável e filtrável)
keplergl_static(map_1)





