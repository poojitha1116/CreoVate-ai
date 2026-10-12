from modules.ai_matching.creators_data import load_creators
from modules.ai_matching.matcher import Brief, recommend, rank_creators, excluded_for_license
from modules.ai_matching.filters import filter_creators, relaxation_hint, get_filter_options

df = load_creators()

# Same shape as the creator dicts in frontend/app.py
FRONTEND_CREATORS = [
    {"id": "CR001", "name": "Sarah Malik", "niches": ["Fashion", "Lifestyle", "Beauty"],
     "content_types": ["Short-form Video", "Carousel"], "engagement": "4.8%", "rate_min": 500, "rate_max": 1200,
     "bio": "Aesthetic beauty walkthroughs, capsule wardrobe styling and viral reels."},
    {"id": "CR004", "name": "Aarav Sharma", "niches": ["Tech", "Gadgets", "AI Tools"],
     "content_types": ["Tutorials", "Long-form Video"], "engagement": "4.1%", "rate_min": 600, "rate_max": 1400,
     "bio": "Deep dives into software suites, cameras and AI workflows."},
]


def test_fashion_reel_brief_ranks_fashion_video_creators_first():
    b = Brief(goal="launch our monsoon fashion collection", audience="young women", content_type="reel",
              niches=["fashion"], style="cinematic", budget=25000, aspect_ratio="9:16")
    top = recommend(df, b, top_n=3)
    assert top[0]["name"] in {"Aarav Mehta", "Sana Qureshi"}
    assert all(0 <= r["score"] <= 100 for r in top)
    assert top[0]["reasons"]


def test_commercial_use_excludes_unlicensed():
    b = Brief(content_type="video", niches=["music"], commercial_use=True)
    assert "Meera Kapoor" not in [r["name"] for r in recommend(df, b, top_n=10)]
    assert "Meera Kapoor" in excluded_for_license(df, b)
    b.commercial_use = False
    assert "Meera Kapoor" in [r["name"] for r in recommend(df, b, top_n=10)]


def test_rank_creators_works_on_frontend_dicts():
    b = Brief(title="Summer Glow", goal="Conversions Vitamin C serum", content_type="Short-form Video",
              niches=["Beauty", "Lifestyle"], style="natural application texture close-ups",
              budget=800, currency="$")
    ranked = rank_creators(FRONTEND_CREATORS, b)
    assert [r["name"] for r in ranked] == ["Sarah Malik", "Aarav Sharma"]
    assert ranked[0]["match_score"] > ranked[1]["match_score"]
    assert ranked[0]["reasons"] and "$500" in " ".join(ranked[0]["reasons"])
    assert "match_score" not in FRONTEND_CREATORS[0]   # originals untouched


def test_filters_and_empty_hint():
    assert len(filter_creators(df, niches=["food"], content_types=["image"])) >= 1
    empty = filter_creators(df, niches=["food"], max_budget=500)
    assert empty.empty
    assert relaxation_hint(df, niches=["food"], max_budget=500)[0].startswith("Remove")


def test_filter_options():
    opts = get_filter_options(df)
    assert "fashion" in opts["niches"] and "video" in opts["content_types"]
