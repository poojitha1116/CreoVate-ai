import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
from modules.ai_matching.matcher import Brief, rank_creators
from modules.ai_matching.db import fetch_creators
from modules.ai_matching.filters import filter_creator_dicts, get_filter_options_from_dicts
from modules.ai_matching.brief_builder import build_brief

# Backwards-compatibility helper for Streamlit < 1.27
def rerun_app():
    if hasattr(st, "rerun"):
        st.rerun()
    elif hasattr(st, "experimental_rerun"):
        st.experimental_rerun()

# 1. Configuration
st.set_page_config(
    page_title="CreoVate_Ai | Intelligent Creator Matching",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. Complete Light Mode SaaS Design System
st.markdown(
    """<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    .stApp {
        background-color: #f8fafc;
        font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
        color: #0f172a;
    }
    
    [data-testid="stSidebar"] { display: none; }
    
    /* Brand Header Title */
    .brand-title {
        font-size: 20px;
        font-weight: 800;
        color: #0f766e;
        letter-spacing: -0.5px;
    }
    
    /* Force All Input Fields, Text Areas & Dropdowns to Clean White */
    div[data-baseweb="input"],
    div[data-baseweb="base-input"],
    div[data-baseweb="select"] > div,
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background-color: #ffffff !important;
        color: #0f172a !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 10px !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03) !important;
    }
    
    /* Input placeholder styling */
    input::placeholder, textarea::placeholder {
        color: #94a3b8 !important;
    }

    /* Input Focus State */
    div[data-baseweb="input"]:focus-within,
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #059669 !important;
        box-shadow: 0 0 0 2px rgba(5, 150, 105, 0.15) !important;
    }

    /* Form Label Styling */
    label[data-testid="stWidgetLabel"] p {
        font-size: 13px !important;
        font-weight: 600 !important;
        color: #334155 !important;
    }
    
    /* Surface Cards */
    .saas-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 22px;
        box-shadow: 0 4px 12px -2px rgba(15, 23, 42, 0.04), 0 2px 6px -1px rgba(15, 23, 42, 0.02);
        margin-bottom: 16px;
    }
    
    /* Hero Feature Banner */
        /* Hide the empty card shells (Streamlit closes the div before the content) */
    .saas-card:empty, .hero-card:empty {
        display: none !important;
    }
    .hero-card {
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
        border-radius: 16px;
        padding: 28px;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.03);
    }
    
    /* Metric Cards */
    .kpi-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 18px 20px;
        box-shadow: 0 2px 4px rgba(15, 23, 42, 0.02);
    }
    .kpi-title {
        font-size: 12px;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .kpi-val {
        font-size: 28px;
        font-weight: 800;
        color: #0f172a;
        margin: 4px 0;
    }
    .kpi-delta {
        font-size: 11px;
        font-weight: 700;
        color: #059669;
    }

    /* Badges */
    .match-pill {
        background: #ecfdf5;
        color: #059669;
        border: 1px solid #a7f3d0;
        padding: 3px 10px;
        border-radius: 9999px;
        font-size: 11px;
        font-weight: 700;
        display: inline-block;
    }
    .tag-pill {
        background: #f1f5f9;
        color: #475569;
        padding: 2px 8px;
        border-radius: 9999px;
        font-size: 11px;
        font-weight: 600;
        margin-right: 4px;
        display: inline-block;
    }

    /* Action Buttons */
    div.stButton > button {
        border-radius: 10px;
        font-weight: 600;
        font-size: 13px;
        padding: 6px 16px;
    }
    </style>""",
    unsafe_allow_html=True
)

# 3. Creator Data Store
DEFAULT_CREATORS = [
    {
        "id": "CR001", "name": "Sarah Malik", "handle": "@sarahcreates",
        "niches": ["Fashion", "Lifestyle", "Beauty"], "content_types": ["Short-form Video", "Carousel"],
        "followers": "1.2M", "engagement": "4.8%", "avg_views": "48k",
        "match_score": 95, "rate_min": 500, "rate_max": 1200,
        "location": "Mumbai, India", "joined": "2021",
        "bio": "Specializes in high-intent aesthetic beauty walkthroughs, capsule wardrobe styling, and viral reels.",
        "avatar": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=200",
        "banner": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=800",
        "reasons": ["Direct category match for Beauty & Fashion", "Proven high video watch completion rate", "Fits well within campaign budget"],
        "recent_work": [
            "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=300",
            "https://images.unsplash.com/photo-1529139574466-a303027c1d8b?w=300",
            "https://images.unsplash.com/photo-1483985988355-763728e1935b?w=300"
        ]
    },
    {
        "id": "CR002", "name": "Rohan Verma", "handle": "@rohanvlogs",
        "niches": ["Travel", "Adventure", "Tech"], "content_types": ["Short-form Video", "Long-form Video"],
        "followers": "850K", "engagement": "4.5%", "avg_views": "62k",
        "match_score": 90, "rate_min": 700, "rate_max": 1500,
        "location": "Delhi, India", "joined": "2022",
        "bio": "Cinematic visual storyteller documenting tech travel setups and backcountry adventures.",
        "avatar": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=200",
        "banner": "https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?w=800",
        "reasons": ["Top creator engagement in Travel & Tech", "Cinematic drone & camera capabilities"],
        "recent_work": [
            "https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=300",
            "https://images.unsplash.com/photo-1503220317375-aaad61436b1b?w=300",
            "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?w=300"
        ]
    },
    {
        "id": "CR003", "name": "Tanya Kapoor", "handle": "@tanyakapoor",
        "niches": ["Fitness", "Health", "Lifestyle"], "content_types": ["Tutorials", "Short-form Video"],
        "followers": "620K", "engagement": "4.2%", "avg_views": "35k",
        "match_score": 87, "rate_min": 400, "rate_max": 900,
        "location": "Bengaluru, India", "joined": "2023",
        "bio": "Certified nutritionist and strength coach sharing realistic daily routines and clean wellness products.",
        "avatar": "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=200",
        "banner": "https://images.unsplash.com/photo-1517838277536-f5f99be501cd?w=800",
        "reasons": ["Strong focus on routine & wellness products", "Consistent active community"],
        "recent_work": [
            "https://images.unsplash.com/photo-1540420773420-3366772f4999?w=300",
            "https://images.unsplash.com/photo-1518611012118-696072aa579a?w=300",
            "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=300"
        ]
    },
    {
        "id": "CR004", "name": "Aarav Sharma", "handle": "@aaravfilms",
        "niches": ["Tech", "Gadgets", "AI Tools"], "content_types": ["Tutorials", "Long-form Video"],
        "followers": "480K", "engagement": "4.1%", "avg_views": "28k",
        "match_score": 84, "rate_min": 600, "rate_max": 1400,
        "location": "Pune, India", "joined": "2020",
        "bio": "Deep dives into cutting-edge software suites, cameras, AI workflows, and desktop productivity.",
        "avatar": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=200",
        "banner": "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=800",
        "reasons": ["High technical clarity for software walkthroughs", "Early adopter audience"],
        "recent_work": [
            "https://images.unsplash.com/photo-1519389950473-47ba0277781c?w=300",
            "https://images.unsplash.com/photo-1531297484001-80022131f5a1?w=300",
            "https://images.unsplash.com/photo-1498050108023-c5249f4df085?w=300"
        ]
    },
    {
        "id": "CR005", "name": "Neha Patel", "handle": "@nehapatelart",
        "niches": ["Food", "Cooking", "Lifestyle"], "content_types": ["Carousel", "Short-form Video"],
        "followers": "390K", "engagement": "4.3%", "avg_views": "22k",
        "match_score": 81, "rate_min": 300, "rate_max": 800,
        "location": "Ahmedabad, India", "joined": "2022",
        "bio": "Quick artisanal cooking guides, balanced meals, and kitchen product demonstrations.",
        "avatar": "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=200",
        "banner": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=800",
        "reasons": ["Cost-efficient conversions", "High saving and bookmark rate"],
        "recent_work": [
            "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=300",
            "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=300",
            "https://images.unsplash.com/photo-1565958011703-44f9829ba187?w=300"
        ]
    },
    {
        "id": "CR006", "name": "Karan Mehta", "handle": "@karancreates",
        "niches": ["Comedy", "Entertainment", "Lifestyle"], "content_types": ["Short-form Video"],
        "followers": "310K", "engagement": "4.0%", "avg_views": "18k",
        "match_score": 78, "rate_min": 350, "rate_max": 750,
        "location": "Mumbai, India", "joined": "2023",
        "bio": "Short sketches, humorous brand integrations, and relatable situational skits.",
        "avatar": "https://images.unsplash.com/photo-1492562080023-ab3db95bfbce?w=200",
        "banner": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=800",
        "reasons": ["High share rate across reels", "Natural brand integration capability"],
        "recent_work": [
            "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?w=300",
            "https://images.unsplash.com/photo-1492684223066-81342ee5ff30?w=300",
            "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=300"
        ]
    }
]

# 4. State Management
if "creators" not in st.session_state:
    st.session_state["creators"] = fetch_creators() or DEFAULT_CREATORS
if "page" not in st.session_state:
    st.session_state["page"] = "Dashboard"
if "selected" not in st.session_state:
    st.session_state["selected"] = st.session_state["creators"][0]
if "shortlist" not in st.session_state:
    st.session_state["shortlist"] = set()
if "campaigns" not in st.session_state:
    st.session_state["campaigns"] = [
        {"name": "Summer Glow Skincare Launch", "niche": "Beauty • Instagram", "status": "Active", "creators": 5, "budget": "$800", "created": "Apr 25, 2026"},
        {"name": "Next-Gen AI Hardware Tour", "niche": "Tech • YouTube", "status": "Matching", "creators": 3, "budget": "$1,200", "created": "Apr 22, 2026"},
        {"name": "Clean Routine Essentials", "niche": "Health • Instagram", "status": "Draft", "creators": 0, "budget": "$500", "created": "Apr 18, 2026"}
    ]

# 5. Top Icon Navigation Header
header_left, header_right = st.columns([1, 4])
with header_left:
    st.markdown("<div style='padding-top:4px;'><span class='brand-title'>✨ CreoVate_Ai</span></div>", unsafe_allow_html=True)

with header_right:
    nav_cols = st.columns([1.1, 1.3, 1.2, 1.4, 1.3, 1.2, 1.8])
    with nav_cols[0]:
        if st.button("🔑 Login", use_container_width=True, type="primary" if st.session_state["page"] == "Login / Sign Up" else "secondary"):
            st.session_state["page"] = "Login / Sign Up"
            rerun_app()
    with nav_cols[1]:
        if st.button("📊 Dashboard", use_container_width=True, type="primary" if st.session_state["page"] == "Dashboard" else "secondary"):
            st.session_state["page"] = "Dashboard"
            rerun_app()
    with nav_cols[2]:
        if st.button("👥 Studio", use_container_width=True, type="primary" if st.session_state["page"] == "Creator Studio" else "secondary"):
            st.session_state["page"] = "Creator Studio"
            rerun_app()
    with nav_cols[3]:
        if st.button("⚡ Brief AI", use_container_width=True, type="primary" if st.session_state["page"] == "Smart Brief Builder" else "secondary"):
            st.session_state["page"] = "Smart Brief Builder"
            rerun_app()
    with nav_cols[4]:
        if st.button("🎯 Matching", use_container_width=True, type="primary" if st.session_state["page"] == "Matching Results" else "secondary"):
            st.session_state["page"] = "Matching Results"
            rerun_app()
    with nav_cols[5]:
        if st.button("👤 Profile", use_container_width=True, type="primary" if st.session_state["page"] == "Creator Profile" else "secondary"):
            st.session_state["page"] = "Creator Profile"
            rerun_app()
    with nav_cols[6]:
        st.markdown("<div style='text-align:right;padding-top:6px;'><span style='color:#10b981;'>●</span> <b>Brand User</b> <span style='color:#94a3b8;font-size:11px;'>@Acme</span></div>", unsafe_allow_html=True)

st.markdown("<hr style='margin:8px 0 24px 0; border:none; border-bottom:1px solid #e2e8f0;'/>", unsafe_allow_html=True)


# ==========================================
# 1. LOGIN / SIGN UP
# ==========================================
if st.session_state["page"] == "Login / Sign Up":
    l1, l2 = st.columns([1, 1], gap="large")
    with l1:
        st.markdown("<div class='hero-card'>", unsafe_allow_html=True)
        st.markdown("<span style='color:#047857;font-size:12px;font-weight:700;letter-spacing:1px;'>AI-POWERED CREATOR PLATFORM</span>", unsafe_allow_html=True)
        st.markdown("<h1 style='color:#0f172a;font-size:32px;margin:8px 0 16px 0;line-height:1.2;'>Connect with creators that move numbers.</h1>", unsafe_allow_html=True)
        st.write("Match campaigns with creators using performance indicators, audience overlap, and verified engagement rates.")
        st.markdown("- ⚡ **Smart Compatibility Engine**: Multi-factor scoring\n- 🛡️ **Verified Creator Metrics**: Real-time engagement and view benchmarks\n- ⏱️ **Fast Turnarounds**: Move from brief formulation to outreach in minutes")
        st.markdown("</div>", unsafe_allow_html=True)
    with l2:
        st.markdown("<div class='saas-card'>", unsafe_allow_html=True)
        st.subheader("Welcome Back")
        st.caption("Sign in to your CreoVate_Ai workspace")
        with st.form("login_form"):
            st.text_input("Work Email", value="you@brand.com")
            st.text_input("Password", type="password", value="••••••••••••")
            st.checkbox("Keep me signed in", value=True)
            if st.form_submit_button("Sign In →", use_container_width=True):
                st.session_state["page"] = "Dashboard"
                rerun_app()
        st.markdown("</div>", unsafe_allow_html=True)


# ==========================================
# 2. DASHBOARD
# ==========================================
elif st.session_state["page"] == "Dashboard":
    st.subheader("Campaign Command Center")
    st.caption("Monitor brand operations, creator recommendations, and live spend metrics.")

    # 4-Column Metric Row
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f'<div class="kpi-card"><div class="kpi-title">Active Campaigns</div><div class="kpi-val">{len(st.session_state["campaigns"])}</div><div class="kpi-delta">↑ +1 added this week</div></div>', unsafe_allow_html=True)
    with m2:
        st.markdown(f'<div class="kpi-card"><div class="kpi-title">Verified Creators</div><div class="kpi-val">{len(st.session_state["creators"])}</div><div class="kpi-delta">↑ +5 added to network</div></div>', unsafe_allow_html=True)
    with m3:
        st.markdown('<div class="kpi-card"><div class="kpi-title">Collaborations</div><div class="kpi-val">2</div><div class="kpi-delta">↑ Active pipeline</div></div>', unsafe_allow_html=True)
    with m4:
        st.markdown('<div class="kpi-card"><div class="kpi-title">Total Spend</div><div class="kpi-val">$2,400</div><div class="kpi-delta">↑ 14% budget remaining</div></div>', unsafe_allow_html=True)

    st.write("")
    c_left, c_right = st.columns([2, 1], gap="medium")

    with c_left:
        st.markdown("<div class='saas-card'>", unsafe_allow_html=True)
        st.markdown("<b style='font-size:15px;color:#0f172a;'>Recent Campaigns</b>", unsafe_allow_html=True)
        st.write("")
        for cmp in st.session_state["campaigns"]:
            r1, r2, r3, r4 = st.columns([3, 1, 1, 1])
            r1.markdown(f"**{cmp['name']}**  \n<span style='font-size:11px;color:#64748b;'>{cmp['niche']}</span>", unsafe_allow_html=True)
            r2.markdown(f"<span class='match-pill'>{cmp['status']}</span>", unsafe_allow_html=True)
            r3.markdown(f"<b>{cmp['budget']}</b>", unsafe_allow_html=True)
            r4.caption(cmp["created"])
            st.markdown("<hr style='margin:8px 0; border:none; border-bottom:1px solid #f1f5f9;'/>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c_right:
        st.markdown("<div class='saas-card'>", unsafe_allow_html=True)
        st.markdown("<b style='font-size:15px;color:#0f172a;'>Top Performing Creators</b>", unsafe_allow_html=True)
        st.write("")
        for c in st.session_state["creators"][:3]:
            tc1, tc2 = st.columns([1, 3])
            tc1.image(c["avatar"], width=46)
            tc2.markdown(f"**{c['name']}**  \n<span style='font-size:11px;color:#64748b;'>{c['followers']} • {c['engagement']} ER</span>", unsafe_allow_html=True)
            st.markdown("<hr style='margin:8px 0; border:none; border-bottom:1px solid #f1f5f9;'/>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)


# ==========================================
# 3. CREATOR STUDIO
# ==========================================
elif st.session_state["page"] == "Creator Studio":
    s_top1, s_top2 = st.columns([3, 1])
    with s_top1:
        st.subheader("Creator Discovery Directory")
        st.caption("Browse curated creator profiles, filter by performance metrics, and review portfolios.")
    with s_top2:
        if st.button("+ Create Campaign Brief", type="primary", use_container_width=True):
            st.session_state["page"] = "Smart Brief Builder"
            rerun_app()

    options = get_filter_options_from_dicts(st.session_state["creators"])

    f1, f2, f3 = st.columns([2, 1, 1])
    q_search = f1.text_input("Search", placeholder="Search name, skill, tool or niche...", label_visibility="collapsed")
    f_niche = f2.multiselect("Niche", options["niches"], placeholder="Niche", label_visibility="collapsed")
    f_type = f3.multiselect("Content type", options["content_types"], placeholder="Content type", label_visibility="collapsed")

    g1, g2, g3, g4 = st.columns([1, 1, 1, 1])
    f_tools = g1.multiselect("Tools", options["tools"], placeholder="Tools", label_visibility="collapsed")
    f_skills = g2.multiselect("Skills", options["skills"], placeholder="Skills", label_visibility="collapsed")
    f_budget = g3.slider("Max budget ($, 0 = any)", 0, 2000, 0, step=50)
    with g4:
        verified_only = st.checkbox("✅ Verified only")
        show_shortlist = st.checkbox("⭐ Show Shortlisted")

    filtered = filter_creator_dicts(
        st.session_state["creators"],
        niches=f_niche, content_types=f_type, tools=f_tools, skills=f_skills,
        max_budget=f_budget, verified_only=verified_only, query=q_search,
    )
    if show_shortlist:
        filtered = [c for c in filtered if c["id"] in st.session_state["shortlist"]]
    if not filtered:
        st.info("No creators match these filters. Try removing one filter.")

    grid_cols = st.columns(3)
    for idx, c in enumerate(filtered):
        with grid_cols[idx % 3]:
            st.markdown("<div class='saas-card'>", unsafe_allow_html=True)
            st.image(c["avatar"], width=62)
            st.markdown(f"**{c['name']} ✓**")
            st.caption(f"{c['handle']} · 👥 {c['followers']} · 📈 {c['engagement']}")
            st.markdown(" ".join([f"<span class='tag-pill'>{n}</span>" for n in (c.get("niches") or [])]), unsafe_allow_html=True)
            st.write("")
            b_fav, b_view = st.columns(2)
            is_faved = c["id"] in st.session_state["shortlist"]
            if b_fav.button("❤️ Shortlisted" if is_faved else "🤍 Shortlist", key=f"fav_{c['id']}", use_container_width=True):
                if is_faved:
                    st.session_state["shortlist"].remove(c["id"])
                else:
                    st.session_state["shortlist"].add(c["id"])
                rerun_app()

            if b_view.button("View Profile", key=f"view_cs_{c['id']}", use_container_width=True):
                st.session_state["selected"] = c
                st.session_state["page"] = "Creator Profile"
                rerun_app()
            st.markdown("</div>", unsafe_allow_html=True)


# ==========================================
# 4. SMART BRIEF BUILDER
# ==========================================
elif st.session_state["page"] == "Smart Brief Builder":
    st.subheader("Smart Campaign Brief Wizard")
    st.caption("Provide campaign requirements to calculate instant match scores across creators.")

    FORMAT_OPTIONS = ["Short-form Video", "Carousel", "Tutorials", "Long-form Video"]
    ASPECT_OPTIONS = ["Any", "9:16", "1:1", "4:5", "16:9"]
    NICHE_OPTIONS = ["Fashion", "Beauty", "Lifestyle", "Tech", "Fitness", "Food", "Travel", "Comedy"]
    GOAL_OPTIONS = ["Brand Awareness", "Conversions", "UGC Production"]

    # Starting values for the form (set once).
    BRIEF_DEFAULTS = {
        "bf_name": "Summer Glow Skincare Launch",
        "bf_brand": "Acme Cosmetics",
        "bf_goal": "Brand Awareness",
        "bf_product": "Organic Vitamin C Serum",
        "bf_niches": ["Beauty", "Lifestyle"],
        "bf_format": "Short-form Video",
        "bf_budget": 800,
        "bf_desc": "Focus on natural application, texture close-ups, and genuine unboxing reactions.",
        "bf_aspect": "Any",
        "bf_commercial": True,
    }
    for k, v in BRIEF_DEFAULTS.items():
        st.session_state.setdefault(k, v)

    def apply_idea():
        """Fill the form fields from the rough idea."""
        b = build_brief(st.session_state.get("bf_idea", ""))
        st.session_state["bf_name"] = b["title"]
        st.session_state["bf_product"] = b["product"]
        st.session_state["bf_goal"] = b["goal"] if b["goal"] in GOAL_OPTIONS else "Brand Awareness"
        st.session_state["bf_niches"] = [n for n in b["niches"] if n in NICHE_OPTIONS]
        st.session_state["bf_format"] = b["content_type"] if b["content_type"] in FORMAT_OPTIONS else "Short-form Video"
        st.session_state["bf_budget"] = max(300, min(2000, int(round(b["budget"] / 50) * 50)))
        st.session_state["bf_aspect"] = b["aspect_ratio"] if b["aspect_ratio"] in ASPECT_OPTIONS else "Any"
        st.session_state["bf_commercial"] = b["commercial_use"]
        st.session_state["bf_desc"] = b["guidelines"]
        st.session_state["bf_notes"] = b["notes"]

    st.markdown("**✨ AI Brief Helper**")
    st.text_area(
        "Describe your idea in your own words",
        key="bf_idea",
        placeholder="Example: We want reels for our new vitamin C serum to boost sales, budget 600 dollars",
    )
    st.button("✨ Fill the form with AI", on_click=apply_idea)
    for note in st.session_state.get("bf_notes", []):
        st.info(note)

    f_col, s_col = st.columns([2, 1], gap="large")
    with f_col:
        st.markdown("<div class='saas-card'>", unsafe_allow_html=True)
        with st.form("brief_form"):
            c_name = st.text_input("Campaign Name *", key="bf_name")
            c_brand = st.text_input("Brand / Company *", key="bf_brand")

            b1, b2 = st.columns(2)
            c_goal = b1.selectbox("Campaign Goal *", GOAL_OPTIONS, key="bf_goal")
            c_product = b2.text_input("Product / Service *", key="bf_product")

            selected_niches = st.multiselect("Target Creator Niches *", NICHE_OPTIONS, key="bf_niches")

            b3, b4 = st.columns(2)
            c_format = b3.selectbox("Format", FORMAT_OPTIONS, key="bf_format")
            c_budget = b4.slider("Budget per Creator ($)", 300, 2000, step=50, key="bf_budget")

            c_desc = st.text_area("Creative Guidelines *", key="bf_desc")

            b5, b6 = st.columns(2)
            c_aspect = b5.selectbox("Aspect Ratio", ASPECT_OPTIONS, key="bf_aspect")
            c_commercial = b6.checkbox("Commercial use required", key="bf_commercial")

            if st.form_submit_button("⚡ Run AI Matching Engine →", use_container_width=True):
                brief = Brief(
                    title=c_name,
                    goal=f"{c_goal} {c_product}",
                    audience=c_brand,
                    content_type=c_format,
                    niches=selected_niches,
                    style=c_desc,
                    budget=c_budget,
                    aspect_ratio="" if c_aspect == "Any" else c_aspect,
                    commercial_use=c_commercial,
                    currency="$",
                )
                recalculated = rank_creators(st.session_state["creators"], brief)
                st.session_state["matches"] = recalculated
                st.session_state["campaigns"].insert(0, {
                    "name": c_name,
                    "niche": f"{selected_niches[0] if selected_niches else 'General'} • Live",
                    "status": "Active",
                    "creators": len(recalculated),
                    "budget": f"${c_budget}",
                    "created": "Today"
                })
                st.session_state["page"] = "Matching Results"
                rerun_app()
        st.markdown("</div>", unsafe_allow_html=True)

    with s_col:
        st.markdown("<div class='saas-card' style='background:#f0fdf4;border-color:#bbf7d0;'>", unsafe_allow_html=True)
        st.markdown("<b style='color:#047857;font-size:13px;'>Algorithmic Scoring Model</b>", unsafe_allow_html=True)
        st.write("")
        st.markdown("- 🎯 **Niche Fit (30%)**\n- 📹 **Content Type (25%)**\n- 🔎 **Brief Keywords (15%)**\n- 💰 **Budget Alignment (15%)**\n- 📐 **Aspect Ratio (10%)**\n- 🛡️ **Trust Signals (5%)**")
        st.write("")
        st.info("The match model recalibrates dynamically as soon as you submit the form.")
        st.markdown("</div>", unsafe_allow_html=True)


# ==========================================
# 5. MATCHING RESULTS
# ==========================================
elif st.session_state["page"] == "Matching Results":
    st.subheader("Ranked Creator Recommendations")
    st.caption("Top matches ranked by compatibility with your active campaign brief.")

    st.tabs(["All Matches", "Instagram", "YouTube", "TikTok"])
    matched_creators = sorted(
        st.session_state.get("matches", st.session_state["creators"]),
        key=lambda x: x.get("match_score") or 0, reverse=True,
    )
    if not matched_creators:
        st.info("No creators matched this brief. Try a different niche, a higher budget, or turn off 'Commercial use required'.")
    res_cols = st.columns(3)
    for idx, c in enumerate(matched_creators):
        with res_cols[idx % 3]:
            st.markdown("<div class='saas-card'>", unsafe_allow_html=True)
            top_l, top_r = st.columns([3, 2])
            with top_l:
                st.image(c["avatar"], width=52)
                st.markdown(f"**{c['name']}**")
                st.caption(f"{c['handle']}")
            with top_r:
                if c.get("match_score") is not None:
                    st.markdown(f"<span class='match-pill'>{c['match_score']}% match</span>", unsafe_allow_html=True)

            st.markdown(" ".join([f"<span class='tag-pill'>{n}</span>" for n in (c.get("niches") or [])]), unsafe_allow_html=True)
            st.caption(f"👥 {c['followers']} · 📈 {c['engagement']} ER")

            for reason in (c.get("reasons") or [])[:3]:
                st.markdown(f"<span style='color:#059669;font-size:11px;font-weight:600;'>✓ {reason}</span>", unsafe_allow_html=True)
            st.write("")
            b_short, b_prof = st.columns(2)
            is_sh = c["id"] in st.session_state["shortlist"]
            if b_short.button("Shortlisted ✓" if is_sh else "Shortlist", key=f"mr_s_{c['id']}", use_container_width=True):
                if is_sh:
                    st.session_state["shortlist"].remove(c["id"])
                else:
                    st.session_state["shortlist"].add(c["id"])
                rerun_app()

            if b_prof.button("View Profile", key=f"mr_p_{c['id']}", use_container_width=True):
                st.session_state["selected"] = c
                st.session_state["page"] = "Creator Profile"
                rerun_app()
            st.markdown("</div>", unsafe_allow_html=True)


# ==========================================
# 6. CREATOR PROFILE
# ==========================================
elif st.session_state["page"] == "Creator Profile":
    selected = st.session_state["selected"]

    if st.button("← Back to Matching Results"):
        st.session_state["page"] = "Matching Results"
        rerun_app()

    st.markdown("<div class='saas-card'>", unsafe_allow_html=True)
    st.image(selected["banner"], width="stretch")

    p_left, p_right = st.columns([3, 1])
    with p_left:
        st.image(selected["avatar"], width=84)
        st.markdown(f"<h3 style='margin:0;color:#0f172a;'>{selected['name']} ✓</h3>", unsafe_allow_html=True)
        st.caption(f"{selected['handle']} • {selected['location']} • Joined {selected['joined']}")
        st.markdown(" ".join([f"<span class='tag-pill'>{n}</span>" for n in (selected.get("niches") or [])]), unsafe_allow_html=True)
    with p_right:
        score = selected.get("match_score")
        if score is not None:
            st.markdown(f"<div style='text-align:center;padding:12px;background:#ecfdf5;border-radius:12px;border:1px solid #a7f3d0;'><h2 style='margin:0;color:#047857;'>{score}%</h2><span style='font-size:11px;color:#047857;font-weight:700;'>MATCH RATING</span></div>", unsafe_allow_html=True)

    st.markdown("<hr style='margin:16px 0; border:none; border-bottom:1px solid #e2e8f0;'/>", unsafe_allow_html=True)

    s1, s2, s3 = st.columns(3)
    s1.metric("Follower Base", selected["followers"])
    s2.metric("Engagement Rate", selected["engagement"])
    s3.metric("Average Views", selected["avg_views"])

    st.markdown("<hr style='margin:16px 0; border:none; border-bottom:1px solid #e2e8f0;'/>", unsafe_allow_html=True)

    st.markdown("**Creator Overview**")
    st.write(selected.get("bio") or "")

    if selected.get("reasons"):
        st.markdown("**Algorithmic Fit Drivers**")
        for r in selected["reasons"]:
            st.markdown(f"- <span style='color:#059669;font-size:12px;'>{r}</span>", unsafe_allow_html=True)

    st.markdown("**Verification**")
    v1, v2, v3 = st.columns(3)
    v1.markdown("✅ Verified tools" if selected.get("verified_tools") else "⚪ Tools not verified")
    v2.markdown("✅ Verified workflow" if selected.get("verified_workflow") else "⚪ Workflow not verified")
    v3.markdown("✅ Verified past work" if selected.get("verified_past_work") else "⚪ Past work not verified")

    if selected.get("specialization"):
        st.markdown(f"**Specialization:** {selected['specialization']}")
    if selected.get("tools"):
        st.markdown("**Tools:** " + " ".join(f"<span class='tag-pill'>{t}</span>" for t in selected["tools"]), unsafe_allow_html=True)
    if selected.get("skills"):
        st.markdown("**Skills:** " + " ".join(f"<span class='tag-pill'>{s}</span>" for s in selected["skills"]), unsafe_allow_html=True)
    if selected.get("workflow"):
        st.markdown(f"**Workflow:** {selected['workflow']}")
    if selected.get("process_evidence"):
        st.caption(f"Process evidence: {selected['process_evidence']}")

    if selected.get("portfolio"):
        st.markdown("**AI Portfolio**")
        for item in selected["portfolio"]:
            tools_used = ", ".join(item.get("tools", []))
            st.markdown(f"- **{item.get('title', 'Untitled')}** ({item.get('type', '')}): {item.get('description', '')}  \n  <span style='font-size:11px;color:#64748b;'>Tools: {tools_used}</span>", unsafe_allow_html=True)

    work = selected.get("recent_work") or []
    if work:
        st.markdown("**Recent Deliverables**")
        pw_cols = st.columns(3)
        for i, url in enumerate(work[:3]):
            pw_cols[i].image(url, width="stretch")

    st.write("")
    b_act1, b_act2 = st.columns(2)
    is_in_shortlist = selected["id"] in st.session_state["shortlist"]
    if b_act1.button("Shortlisted ✓" if is_in_shortlist else "Shortlist", use_container_width=True):
        if is_in_shortlist:
            st.session_state["shortlist"].remove(selected["id"])
        else:
            st.session_state["shortlist"].add(selected["id"])
        rerun_app()

    if b_act2.button("Initiate Outreach Channel →", type="primary", use_container_width=True):
        st.success(f"Collaboration channel initiated with {selected['name']}!")
    st.markdown("</div>", unsafe_allow_html=True)
