"""Turn a rough campaign idea into a structured brief (rule-based, no API key)."""
import re

# Names match the options in the Smart Brief form.
NICHE_WORDS = {
    "Beauty": ["skincare", "serum", "makeup", "beauty", "cosmetic", "lipstick", "glow"],
    "Fashion": ["fashion", "outfit", "clothing", "wardrobe", "apparel", "style"],
    "Lifestyle": ["lifestyle", "daily", "routine", "home"],
    "Tech": ["tech", "gadget", "app", "software", "laptop", "phone", "hardware", "ai"],
    "Fitness": ["fitness", "workout", "gym", "protein", "wellness", "health"],
    "Food": ["food", "recipe", "cooking", "snack", "drink", "coffee", "restaurant"],
    "Travel": ["travel", "trip", "hotel", "tour", "adventure"],
    "Comedy": ["comedy", "funny", "skit", "meme", "humor"],
}

FORMAT_WORDS = {
    "Short-form Video": ["reel", "reels", "short", "shorts", "tiktok"],
    "Carousel": ["carousel", "slides", "slideshow"],
    "Tutorials": ["tutorial", "how to", "walkthrough", "explainer"],
    "Long-form Video": ["youtube", "long video", "documentary", "review"],
}

DEFAULT_ASPECT = {
    "Short-form Video": "9:16",
    "Carousel": "4:5",
    "Tutorials": "16:9",
    "Long-form Video": "16:9",
}

GOAL_WORDS = {
    "Conversions": ["sales", "sell", "buy", "convert", "conversion", "purchase", "discount"],
    "UGC Production": ["ugc", "user generated", "user-generated", "testimonial"],
}


def _words(text: str) -> set:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _has(text: str, words) -> bool:
    found = _words(text)
    return any((w in found) if " " not in w else (w in text.lower()) for w in words)


def _find_budget(text: str):
    t = text.lower().replace(",", "")
    patterns = [
        r"(?:\$|usd\s?|inr\s?|rs\.?\s?|₹)\s?(\d+(?:\.\d+)?)\s?(k)?",
        r"(\d+(?:\.\d+)?)\s?(k)?\s?(?:dollars|usd|inr|rupees|rs)\b",
    ]
    for p in patterns:
        m = re.search(p, t)
        if m:
            value = float(m.group(1)) * (1000 if m.group(2) else 1)
            return int(value)
    return None


def build_brief(idea: str) -> dict:
    """Return brief fields for the Smart Brief form, plus notes about missing info."""
    text = (idea or "").strip()
    notes = []

    niches = [n for n, words in NICHE_WORDS.items() if _has(text, words)]
    if not niches:
        niches = ["Lifestyle"]
        notes.append("No niche found in your idea, so I guessed Lifestyle. Please check it.")

    content_type = "Short-form Video"
    for name, words in FORMAT_WORDS.items():
        if _has(text, words):
            content_type = name
            break

    ratio = re.search(r"\b(9:16|16:9|1:1|4:5)\b", text)
    aspect = ratio.group(1) if ratio else DEFAULT_ASPECT[content_type]

    goal = "Brand Awareness"
    for name, words in GOAL_WORDS.items():
        if _has(text, words):
            goal = name
            break

    budget = _find_budget(text)
    if budget is None:
        budget = 800
        notes.append("No budget found, so I used 800. Please set your own.")
    budget = max(300, min(2000, budget))  # same range as the form slider


    lowered = text.lower()
    commercial = not ("personal use" in lowered or "no commercial" in lowered)

    # Product name: the words after "for our new ...", "promote ...", "launch ...".
    product = ""
    m = re.search(
        r"\b(?:for|promote|promoting|launch|launching)\s+(?:our|my|the|a|an)?\s*(?:new\s+)?"
        r"([a-z0-9][a-z0-9 \-]*?)(?=\s+(?:to|and|with|for|on|in|so|that)\b|[,.;]|$)",
        text, flags=re.IGNORECASE,
    )
    if m:
        product = m.group(1).strip().title()
    if not product:
        product = f"{niches[0]} {content_type}"
    title = f"{product} Campaign"

    guidelines = (
        f"{text.rstrip(' .,;')}. "
        f"Deliver as {content_type} in {aspect}. "
        "Show the product clearly in the first 3 seconds, keep the tone natural and honest, "
        "and end with a clear call to action."
    ).strip()
    if commercial:
        guidelines += " Commercial use rights are required."

    return {
        "title": title,
        "goal": goal,
        "product": product,
        "niches": niches,
        "content_type": content_type,
        "budget": budget,
        "aspect_ratio": aspect,
        "commercial_use": commercial,
        "guidelines": guidelines,
        "notes": notes,
    }