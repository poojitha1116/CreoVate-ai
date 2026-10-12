from modules.ai_matching.creators_data import load_creators
from modules.ai_matching.matcher import Brief, recommend, excluded_for_license
from modules.ai_matching.filters import filter_creators, relaxation_hint, get_filter_options
df = load_creators()


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


def test_filters_and_empty_hint():
    assert len(filter_creators(df, niches=["food"], content_types=["image"])) >= 1
    empty = filter_creators(df, niches=["food"], max_budget=500)
    assert empty.empty
    assert relaxation_hint(df, niches=["food"], max_budget=500)[0].startswith("Remove")


def test_filter_options():
    opts = get_filter_options(df)
    assert "fashion" in opts["niches"] and "video" in opts["content_types"]
