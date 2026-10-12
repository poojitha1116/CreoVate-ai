"""Rule-based creator matching. Returns a 0-100 score with an explanation."""
import re
from dataclasses import dataclass, field
from typing import List

import pandas as pd

# Points per criterion; must sum to 100.
WEIGHTS = {"niche": 30, "content_type": 25, "keywords": 15, "budget": 15, "format": 10, "trust": 5}

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
    budget: float = 0            # INR, 0 = not specified
    aspect_ratio: str = ""       # e.g. "9:16", "" = not specified
    commercial_use: bool = True  # True = creator must offer a commercial license


def _tokens(text: str) -> set:
    return {t for t in re.findall(r"[a-z0-9]+", str(text).lower()) if t not in STOPWORDS and len(t) > 2}


def _lower(items) -> List[str]:
    return [str(i).lower() for i in items]


def _niche_score(c, b):
    if not b.niches:
        return 0.5, None
    wanted, have = set(_lower(b.niches)), set(_lower(c["niches"]))
    hit = wanted & have
    if hit:
        return len(hit) / len(wanted), f"Works in your niche: {', '.join(sorted(hit))}"
    return 0.0, None


def _type_score(c, b):
    want, have = b.content_type.lower(), _lower(c["content_types"])
    if want in have:
        return 1.0, f"Creates {want} content"
    best = max((RELATED_TYPES.get(want, {}).get(h, 0) for h in have), default=0)
    return best, (f"Creates related formats ({', '.join(have)})" if best else None)


def _keyword_score(c, b):
    target = _tokens(f"{b.goal} {b.audience} {b.style} {b.title}")
    if not target:
        return 0.5, None
    pool = _tokens(" ".join(c["skills"] + c["tools"] + c["niches"] + [c["specialization"], c["workflow"]]))
    hit = target & pool
    if not hit:
        return 0.0, None
    return min(1.0, len(hit) / 3), f"Brief keywords match their skills: {', '.join(sorted(hit)[:4])}"


def _budget_score(c, b):
    if b.budget <= 0:
        return 0.5, None
    lo, hi = c["rate_min"], c["rate_max"]
    if b.budget >= lo:
        return 1.0, f"Budget fits their range (Rs {lo:,} to Rs {hi:,})"
    ratio = b.budget / lo
    if ratio < 0.6:
        return 0.0, None
    return (ratio - 0.6) / 0.4, f"Budget is slightly below their usual starting rate (Rs {lo:,})"


def _format_score(c, b):
    if not b.aspect_ratio:
        return 0.5, None
    ok = b.aspect_ratio in c["formats"]
    return (1.0, f"Delivers {b.aspect_ratio}") if ok else (0.0, None)


def _trust_score(c, b):
    s = (0.4 if c["verified_tools"] else 0) + (0.4 if c["verified_past_work"] else 0) + (0.2 if c["rating"] >= 4.5 else 0)
    parts = []
    if c["verified_tools"]:
        parts.append("verified tools")
    if c["verified_past_work"]:
        parts.append("verified past work")
    return s, (f"Trust signals: {', '.join(parts)}" if parts else None)


SCORERS = {"niche": _niche_score, "content_type": _type_score, "keywords": _keyword_score,
           "budget": _budget_score, "format": _format_score, "trust": _trust_score}


def score_creator(creator, brief: Brief) -> dict:
    """creator: dict-like row. Returns score, per-criterion points and reasons."""
    breakdown, reasons = {}, []
    for name, fn in SCORERS.items():
        frac, reason = fn(creator, brief)
        breakdown[name] = round(frac * WEIGHTS[name], 1)
        if reason:
            reasons.append(reason)
    return {"id": creator["id"], "name": creator["name"], "score": round(sum(breakdown.values())),
            "breakdown": breakdown, "reasons": reasons, "creator": dict(creator)}


def excluded_for_license(df: pd.DataFrame, brief: Brief) -> List[str]:
    if not brief.commercial_use:
        return []
    return df.loc[~df["commercial_license"], "name"].tolist()


def recommend(df: pd.DataFrame, brief: Brief, top_n: int = 5, min_score: int = 0) -> List[dict]:
    """Rank creators for a brief. Creators without a commercial license are
    excluded when the brief requires commercial use."""
    pool = df[df["commercial_license"]] if brief.commercial_use else df
    results = [score_creator(row, brief) for _, row in pool.iterrows()]
    results = [r for r in results if r["score"] >= min_score]
    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:top_n]
