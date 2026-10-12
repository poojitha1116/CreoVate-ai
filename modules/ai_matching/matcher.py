"""Rule-based creator matching. Scores a creator 0-100 against a campaign brief.

Works on plain dicts, so it accepts both the seed data (creators_data.py)
and the frontend's own creator dicts. Missing fields are handled gracefully.
"""
import re
from dataclasses import dataclass, field
from typing import List

import pandas as pd

# Points per criterion; must sum to 100.
WEIGHTS = {"niche": 30, "content_type": 25, "keywords": 15, "budget": 15, "format": 10, "trust": 5}

# Frontend labels -> canonical types used for "related format" credit.
CANONICAL_TYPES = {
    "short-form video": "reel", "short form video": "reel", "long-form video": "video",
    "tutorials": "video", "tutorial": "video", "carousel": "graphic", "photo": "image",
}

# Content types that are close enough to earn partial credit.
RELATED_TYPES = {
    "video": {"reel": 0.6, "animation": 0.5},
    "reel": {"video": 0.6},
    "animation": {"video": 0.5, "graphic": 0.3},
    "image": {"graphic": 0.7},
    "graphic": {"image": 0.7, "animation": 0.3},
}

STOPWORDS = {"the", "a", "an", "and", "or", "for", "to", "of", "in", "on", "with", "our", "we", "want",
             "need", "make", "that", "this", "is", "are", "be", "it", "their", "your", "my", "at", "by", "from"}


@dataclass
class Brief:
    title: str = ""
    goal: str = ""
    audience: str = ""
    content_type: str = "video"
    niches: List[str] = field(default_factory=list)
    style: str = ""
    budget: float = 0            # 0 = not specified
    aspect_ratio: str = ""       # e.g. "9:16"; "" = not specified
    commercial_use: bool = True  # True = creator must offer a commercial license
    currency: str = "₹"          # symbol used in explanations


def _tokens(text: str) -> set:
    return {t for t in re.findall(r"[a-z0-9]+", str(text).lower()) if t not in STOPWORDS and len(t) > 2}


def _lower(items) -> List[str]:
    return [str(i).lower() for i in (items if items is not None else [])]


def _canon(t: str) -> str:
    t = str(t).lower().strip()
    return CANONICAL_TYPES.get(t, t)


def _pct(value) -> float:
    try:
        return float(str(value).strip().rstrip("%"))
    except ValueError:
        return 0.0


def _list(c, key) -> list:
    v = c.get(key, [])
    return list(v) if v is not None and not isinstance(v, float) else []


def _niche_score(c, b):
    if not b.niches:
        return 0.5, None
    wanted, have = set(_lower(b.niches)), set(_lower(_list(c, "niches")))
    hit = wanted & have
    if hit:
        return len(hit) / len(wanted), f"Works in your niche: {', '.join(sorted(hit))}"
    return 0.0, None


def _type_score(c, b):
    want = b.content_type.lower().strip()
    have = _lower(_list(c, "content_types"))
    if want in have:
        return 1.0, f"Creates {b.content_type} content"
    cw, chave = _canon(want), {_canon(h) for h in have}
    if cw in chave:
        return 0.8, f"Creates closely related content ({', '.join(have)})"
    best = max((RELATED_TYPES.get(cw, {}).get(h, 0) for h in chave), default=0)
    return best, (f"Creates related formats ({', '.join(have)})" if best else None)


def _keyword_score(c, b):
    target = _tokens(f"{b.goal} {b.audience} {b.style} {b.title}")
    if not target:
        return 0.5, None
    text = " ".join(_list(c, "skills") + _list(c, "tools") + _list(c, "niches") + _list(c, "content_types")
                    + [str(c.get(k, "")) for k in ("specialization", "workflow", "bio")])
    hit = target & _tokens(text)
    if not hit:
        return 0.0, None
    return min(1.0, len(hit) / 3), f"Brief keywords match their profile: {', '.join(sorted(hit)[:4])}"


def _budget_score(c, b):
    lo, hi = c.get("rate_min"), c.get("rate_max")
    if b.budget <= 0 or lo is None or hi is None:
        return 0.5, None
    cur = b.currency
    if b.budget >= lo:
        return 1.0, f"Budget fits their range ({cur}{lo:,} to {cur}{hi:,})"
    ratio = b.budget / lo
    if ratio < 0.6:
        return 0.0, None
    return (ratio - 0.6) / 0.4, f"Budget is slightly below their usual starting rate ({cur}{lo:,})"


def _format_score(c, b):
    formats = _list(c, "formats")
    if not b.aspect_ratio or not formats:
        return 0.5, None
    ok = b.aspect_ratio in formats
    return (1.0, f"Delivers {b.aspect_ratio}") if ok else (0.0, None)


def _trust_score(c, b):
    tools_ok = bool(_list(c, "verified_tools"))
    work_ok = bool(c.get("verified_past_work", False))
    rating = c.get("rating", 0)
    strong = (rating if isinstance(rating, (int, float)) else 0) >= 4.5 or _pct(c.get("engagement")) >= 4.5
    s = 0.4 * tools_ok + 0.4 * work_ok + 0.2 * strong
    parts = [name for ok, name in ((tools_ok, "verified tools"), (work_ok, "verified past work"),
                                   (strong, "strong rating or engagement")) if ok]
    return s, (f"Trust signals: {', '.join(parts)}" if parts else None)


SCORERS = {"niche": _niche_score, "content_type": _type_score, "keywords": _keyword_score,
           "budget": _budget_score, "format": _format_score, "trust": _trust_score}


def score_creator(creator, brief: Brief) -> dict:
    """creator: dict-like. Returns score, per-criterion points and reasons."""
    breakdown, reasons = {}, []
    for name, fn in SCORERS.items():
        frac, reason = fn(creator, brief)
        breakdown[name] = round(frac * WEIGHTS[name], 1)
        if reason:
            reasons.append(reason)
    return {"id": creator.get("id"), "name": creator.get("name"), "score": round(sum(breakdown.values())),
            "breakdown": breakdown, "reasons": reasons, "creator": dict(creator)}


def rank_creators(creators: List[dict], brief: Brief, min_score: int = 0) -> List[dict]:
    """Frontend-friendly ranking. Takes a list of creator dicts and returns copies
    with 'match_score', 'reasons' and 'score_breakdown' filled in, best first.
    Creators without a commercial license are dropped when the brief needs one
    (creators with no such field are assumed to be licensed)."""
    out = []
    for c in creators:
        if brief.commercial_use and not c.get("commercial_license", True):
            continue
        r = score_creator(c, brief)
        if r["score"] < min_score:
            continue
        item = dict(c)
        item["match_score"] = r["score"]
        item["reasons"] = r["reasons"] or ["No strong signals matched this brief"]
        item["score_breakdown"] = r["breakdown"]
        out.append(item)
    return sorted(out, key=lambda x: x["match_score"], reverse=True)


def excluded_for_license(df: pd.DataFrame, brief: Brief) -> List[str]:
    if not brief.commercial_use or "commercial_license" not in df:
        return []
    return df.loc[~df["commercial_license"], "name"].tolist()


def recommend(df: pd.DataFrame, brief: Brief, top_n: int = 5, min_score: int = 0) -> List[dict]:
    """DataFrame version of rank_creators; returns score/reasons/breakdown dicts."""
    pool = df[df["commercial_license"]] if (brief.commercial_use and "commercial_license" in df) else df
    results = [score_creator(row, brief) for _, row in pool.iterrows()]
    results = [r for r in results if r["score"] >= min_score]
    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:top_n]
