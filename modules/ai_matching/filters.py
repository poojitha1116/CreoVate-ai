"""Search and filtering for the creator list."""
from typing import Dict, List, Optional

import pandas as pd


def _any_match(values, wanted, substring=False) -> bool:
    values = [str(v).lower() for v in values]
    for w in (str(x).lower() for x in wanted):
        if substring and any(w in v for v in values):
            return True
        if not substring and w in values:
            return True
    return False


def filter_creators(df: pd.DataFrame, niches=None, skills=None, content_types=None, tools=None,
                    max_budget: Optional[float] = None, verified_only=False, commercial_only=False,
                    query: str = "") -> pd.DataFrame:
    out = df
    if niches:
        out = out[out["niches"].apply(lambda v: _any_match(v, niches))]
    if content_types:
        out = out[out["content_types"].apply(lambda v: _any_match(v, content_types))]
    if skills:
        out = out[out["skills"].apply(lambda v: _any_match(v, skills, substring=True))]
    if tools:
        out = out[out["tools"].apply(lambda v: _any_match(v, tools))]
    if max_budget:
        out = out[out["rate_min"] <= max_budget]
    if verified_only:
        out = out[out["verified_tools"].apply(bool) | out["verified_past_work"]]
    if commercial_only:
        out = out[out["commercial_license"]]
    if query:
        q = query.lower()
        blob = out.apply(lambda r: " ".join([r["name"], r["specialization"], *r["skills"], *r["tools"], *r["niches"]]).lower(), axis=1)
        out = out[blob.str.contains(q, regex=False)]
    return out


def relaxation_hint(df: pd.DataFrame, **filters) -> List[str]:
    """For an empty result: which single filter, if removed, would bring creators back."""
    active = {k: v for k, v in filters.items() if v}
    hints = []
    for key in active:
        relaxed = {k: v for k, v in active.items() if k != key}
        n = len(filter_creators(df, **relaxed))
        if n:
            hints.append(f"Remove the '{key}' filter to see {n} creator(s).")
    return hints or ["No creators in the database yet."]


def get_filter_options(df: pd.DataFrame) -> Dict[str, List[str]]:
    """Values for the frontend's dropdowns."""
    def uniq(col):
        return sorted({x for items in df[col] for x in items})
    return {"niches": uniq("niches"), "skills": uniq("skills"), "tools": uniq("tools"),
            "content_types": uniq("content_types"), "formats": uniq("formats")}


def _as_list(value) -> list:
    """Turn None, a single value or a list into a clean list of strings."""
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(v) for v in value]
    return [str(value)]


def filter_creator_dicts(creators, niches=None, skills=None, content_types=None, tools=None,
                         max_budget=None, verified_only=False, query: str = "") -> list:
    """Same filters as filter_creators, but for a list of creator dicts.
    Safe when a field is None or missing."""
    out = []
    for c in creators:
        if niches and not _any_match(_as_list(c.get("niches")), niches):
            continue
        if content_types and not _any_match(_as_list(c.get("content_types")), content_types):
            continue
        if skills and not _any_match(_as_list(c.get("skills")), skills, substring=True):
            continue
        if tools and not _any_match(_as_list(c.get("tools")), tools):
            continue
        if max_budget and (c.get("rate_min") or 0) > max_budget:
            continue
        if verified_only and not (c.get("verified_tools") or c.get("verified_past_work") or c.get("verified_workflow")):
            continue
        if query:
            blob = " ".join([str(c.get("name") or ""), str(c.get("specialization") or ""),
                             *_as_list(c.get("skills")), *_as_list(c.get("tools")),
                             *_as_list(c.get("niches"))]).lower()
            if query.lower() not in blob:
                continue
        out.append(c)
    return out


def get_filter_options_from_dicts(creators) -> dict:
    """Values for the dropdowns, taken from a list of creator dicts."""
    def uniq(key):
        return sorted({x for c in creators for x in _as_list(c.get(key))})
    return {k: uniq(k) for k in ("niches", "skills", "tools", "content_types")}