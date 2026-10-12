
import streamlit as st
import pandas as pd

from modules.creator_studio.creator_studio import show_creator_studio


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------
st.set_page_config(
    page_title="Prismatch",
    page_icon="✨",
    layout="wide"
)


# --------------------------------------------------
# APPLICATION HEADER
# --------------------------------------------------
st.title("✨ Prismatch")
st.subheader("AI-Native Creator Marketplace")

st.write(
    "Helping brands discover creators who match their "
    "campaign goals, creative style, and budget."
)


# --------------------------------------------------
# SAMPLE CREATOR DATA
# --------------------------------------------------
creators = pd.DataFrame([
    {
        "Creator": "Aarav Sharma",
        "Category": "Fitness",
        "Platform": "Instagram",
        "AI Tools": "Canva AI, ChatGPT",
        "Budget (₹)": 5000
    },
    {
        "Creator": "Meera Reddy",
        "Category": "Technology",
        "Platform": "YouTube",
        "AI Tools": "Runway, ChatGPT",
        "Budget (₹)": 8000
    },
    {
        "Creator": "Kabir Verma",
        "Category": "Lifestyle",
        "Platform": "Instagram",
        "AI Tools": "Midjourney, Canva AI",
        "Budget (₹)": 3500
    },
    {
        "Creator": "Ananya Rao",
        "Category": "Education",
        "Platform": "YouTube",
        "AI Tools": "ChatGPT, Canva AI",
        "Budget (₹)": 4500
    }
])


# --------------------------------------------------
# SIDEBAR NAVIGATION
# --------------------------------------------------
st.sidebar.title("Navigation")

page = st.sidebar.radio(
    "Choose a page",
    [
        "Dashboard",
        "Creator Studio",
        "Smart Brief Builder"
    ]
)


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------
if page == "Dashboard":
    st.header("📊 Marketplace Dashboard")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Sample Creators",
        len(creators)
    )

    col2.metric(
        "Categories",
        creators["Category"].nunique()
    )

    col3.metric(
        "Platforms",
        creators["Platform"].nunique()
    )

    st.subheader("Featured Creators")

    st.dataframe(
        creators,
        use_container_width=True,
        hide_index=True
    )


# --------------------------------------------------
# CREATOR STUDIO
# --------------------------------------------------
elif page == "Creator Studio":
    show_creator_studio(creators)


# --------------------------------------------------
# SMART BRIEF BUILDER
# --------------------------------------------------
elif page == "Smart Brief Builder":
    st.header("📝 Create Your Campaign Brief")

    st.write(
        "Describe your campaign and select your preferred "
        "creator requirements."
    )

    campaign = st.text_area(
        "Describe your campaign",
        placeholder=(
            "Example: Promote an affordable fitness product "
            "to college students."
        )
    )

    category = st.selectbox(
        "Preferred creator category",
        sorted(creators["Category"].unique().tolist())
    )

    platform = st.selectbox(
        "Preferred platform",
        sorted(creators["Platform"].unique().tolist())
    )

    budget = st.number_input(
        "Maximum budget (₹)",
        min_value=500,
        value=5000,
        step=500
    )

    if st.button("🔎 Find Matching Creators", type="primary"):

        if not campaign.strip():
            st.warning(
                "Please describe your campaign first."
            )

        else:
            matches = creators[
                (creators["Category"] == category)
                & (creators["Platform"] == platform)
                & (creators["Budget (₹)"] <= budget)
            ]

            if matches.empty:
                st.info(
                    "No exact matches found. Try changing "
                    "your category, platform, or budget."
                )

            else:
                st.success(
                    f"Found {len(matches)} matching creators!"
                )

                st.dataframe(
                    matches,
                    use_container_width=True,
                    hide_index=True
                )

                st.caption(
                    "Matches currently use category, platform, "
                    "and budget filters. AI-based semantic "
                    "matching will be added in a later step."
                )


# --------------------------------------------------
# FOOTER
# --------------------------------------------------
st.divider()

st.caption(
    "Prismatch | AI-Native Creator Marketplace | "
    "Hackathon Prototype"
)
