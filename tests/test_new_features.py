from modules.ai_matching.brief_builder import build_brief
from modules.ai_matching.filters import filter_creator_dicts, get_filter_options_from_dicts

CREATORS = [
    {"id": "A", "name": "Ann", "niches": ["Beauty"], "skills": ["styling"], "tools": ["Canva"],
     "content_types": ["Carousel"], "rate_min": 500, "verified_tools": ["Canva"], "verified_past_work": False},
    {"id": "B", "name": "Bob", "niches": None, "skills": None, "tools": None,
     "content_types": None, "rate_min": None, "verified_tools": [], "verified_past_work": False},
]


def test_filter_by_niche():
    result = filter_creator_dicts(CREATORS, niches=["beauty"])
    assert [c["id"] for c in result] == ["A"]


def test_filter_handles_empty_values():
    # No filters: everything comes back, and None fields do not crash.
    assert len(filter_creator_dicts(CREATORS)) == 2
    assert len(filter_creator_dicts(CREATORS, query="ann")) == 1


def test_filter_verified_only():
    result = filter_creator_dicts(CREATORS, verified_only=True)
    assert [c["id"] for c in result] == ["A"]


def test_filter_options_skip_none():
    options = get_filter_options_from_dicts(CREATORS)
    assert options["niches"] == ["Beauty"]
    assert options["tools"] == ["Canva"]


def test_build_brief_from_rough_idea():
    b = build_brief("We want reels for our new vitamin C skincare serum to boost sales, budget 600 dollars")
    assert b["niches"] == ["Beauty"]
    assert b["content_type"] == "Short-form Video"
    assert b["goal"] == "Conversions"
    assert b["budget"] == 600
    assert b["aspect_ratio"] == "9:16"
    assert "Serum" in b["product"]


def test_build_brief_empty_idea_uses_defaults():
    b = build_brief("")
    assert b["budget"] == 800
    assert b["notes"]  # tells the user what was guessed