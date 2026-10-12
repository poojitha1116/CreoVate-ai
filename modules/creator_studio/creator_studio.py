
import streamlit as st
import pandas as pd


def show_creator_studio(creators):
    st.header("🎨 Creator Studio")
    st.write(
        "Discover AI creators by specialization, platform, "
        "creative tools, and budget."
    )

    col1, col2 = st.columns(2)

    with col1:
        categories = ["All"] + sorted(
            creators["Category"].unique().tolist()
        )
        category = st.selectbox("Specialization", categories)

    with col2:
        platforms = ["All"] + sorted(
            creators["Platform"].unique().tolist()
        )
        platform = st.selectbox("Platform", platforms)

    filtered = creators.copy()

    if category != "All":
        filtered = filtered[
            filtered["Category"] == category
        ]

    if platform != "All":
        filtered = filtered[
            filtered["Platform"] == platform
        ]

    st.subheader(f"Creators found: {len(filtered)}")

    if filtered.empty:
        st.info("No creators match these filters.")
    else:
        st.dataframe(
            filtered,
            use_container_width=True,
            hide_index=True
        )

        st.caption(
            "Demo profiles use sample data; verification "
            "and portfolio evidence will be added next."
        )
