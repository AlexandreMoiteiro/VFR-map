import streamlit as st
import pandas as pd
import plotly.express as px

CSV_PATH = "significant_places.csv"
df = pd.read_csv(CSV_PATH)
df["LatDecimal"] = pd.to_numeric(df["LatDecimal"], errors="coerce")
df["LonDecimal"] = pd.to_numeric(df["LonDecimal"], errors="coerce")
df = df.dropna(subset=["LatDecimal", "LonDecimal"])

search = st.text_input("Filtra por nome ou código", "")
if search:
    df = df[df['Name'].str.contains(search, case=False) | df['Code'].str.contains(search, case=False)]

st.title("Significant VFR Points in Portugal (Plotly Express)")
st.write(f"Total de pontos no mapa: {len(df)}")

with st.expander("Show Data Table"):
    st.dataframe(df[['Name', 'Code', 'LatDecimal', 'LonDecimal']])

fig = px.scatter_mapbox(
    df,
    lat="LatDecimal",
    lon="LonDecimal",
    hover_name="Name",
    hover_data=["Code"],
    zoom=6,
    height=700
)
fig.update_layout(mapbox_style="open-street-map")  # Sem token!
fig.update_traces(marker=dict(size=8, color="red"))

st.plotly_chart(fig, use_container_width=True)





