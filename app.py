import streamlit as st
import pandas as pd
import pydeck as pdk

# Upload or use your CSV (for local dev, replace with file path)
CSV_PATH = "significant_places.csv"

# Title and info
st.title("Significant VFR Points in Portugal")
st.markdown("Interactive map of significant VFR points (visual reporting points) for VFR navigation.")

# Read data
df = pd.read_csv(CSV_PATH)

# Optional filter by name or code
search = st.text_input("Filter by Name or Code", "")
if search:
    df = df[df['Name'].str.contains(search, case=False) | df['Code'].str.contains(search, case=False)]

# Show table
with st.expander("Show Data Table"):
    st.dataframe(df[['Name', 'Code', 'LatDecimal', 'LonDecimal']])

# Map
st.pydeck_chart(
    pdk.Deck(
        map_style="mapbox://styles/mapbox/light-v9",
        initial_view_state=pdk.ViewState(
            latitude=df['LatDecimal'].mean(),
            longitude=df['LonDecimal'].mean(),
            zoom=6.5,
            pitch=0,
        ),
        layers=[
            pdk.Layer(
                "ScatterplotLayer",
                data=df,
                get_position='[LonDecimal, LatDecimal]',
                get_color='[200, 30, 0, 160]',
                get_radius=1000,
                pickable=True,
                auto_highlight=True,
            ),
            pdk.Layer(
                "TextLayer",
                data=df,
                get_position='[LonDecimal, LatDecimal]',
                get_text="Code",
                get_size=16,
                get_color=[0, 0, 0],
                get_angle=0,
                get_alignment_baseline="'bottom'",
            ),
        ],
        tooltip={"text": "{Name}\nCode: {Code}\nLat: {LatDecimal}\nLon: {LonDecimal}"},
    )
)

st.info("Click on the points to see details. Use the filter above to quickly find a specific VFR point by name or code.")




