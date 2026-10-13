"""Upload the 6 default creators to Supabase (run this once).

Reads DEFAULT_CREATORS from frontend/app.py, adds the extra fields the
matcher needs, and saves them in the "creators" table.
"""
import ast
import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

APP_FILE = ROOT / "frontend" / "app.py"

# Only these keys exist as columns in the table.
COLUMNS = {
    "id", "name", "handle", "location", "joined", "bio", "specialization",
    "workflow", "niches", "skills", "tools", "content_types", "formats",
    "followers", "engagement", "avg_views", "rate_min", "rate_max",
    "turnaround_days", "commercial_license", "verified_tools",
    "verified_past_work", "rating", "avatar", "banner", "recent_work",
    "portfolio", "verified_workflow", "process_evidence",
}

# Extra fields for the matcher, one block per creator.
EXTRA = {
    "CR001": {
        "specialization": "Fashion and beauty creator",
        "workflow": "Phone shoot, CapCut edit, scheduled reel posts",
        "skills": ["styling", "short form video", "trend content", "social media"],
        "tools": ["CapCut", "Canva", "Midjourney"],
        "formats": ["9:16", "4:5"],
        "turnaround_days": 3, "commercial_license": True,
        "verified_tools": ["Canva"], "verified_past_work": True, "rating": 4.8,
    },
    "CR002": {
        "specialization": "Travel and tech filmmaker",
        "workflow": "Drone and camera shoot, Premiere Pro edit, color grade",
        "skills": ["cinematic video", "drone footage", "color grading", "storytelling"],
        "tools": ["Premiere Pro", "DaVinci Resolve", "Runway"],
        "formats": ["16:9", "9:16"],
        "turnaround_days": 7, "commercial_license": True,
        "verified_tools": ["Runway"], "verified_past_work": True, "rating": 4.6,
    },
    "CR003": {
        "specialization": "Fitness and wellness coach",
        "workflow": "Gym shoot, tutorial script, quick edit and captions",
        "skills": ["tutorials", "short form video", "wellness", "social media"],
        "tools": ["CapCut", "Canva"],
        "formats": ["9:16", "1:1"],
        "turnaround_days": 4, "commercial_license": True,
        "verified_tools": [], "verified_past_work": True, "rating": 4.4,
    },
    "CR004": {
        "specialization": "Tech and AI tools explainer",
        "workflow": "Screen recording, voiceover, tutorial edit",
        "skills": ["tutorials", "explainer", "voiceover", "scriptwriting"],
        "tools": ["Runway", "ElevenLabs", "Premiere Pro"],
        "formats": ["16:9", "1:1"],
        "turnaround_days": 6, "commercial_license": True,
        "verified_tools": ["Runway", "ElevenLabs"], "verified_past_work": True, "rating": 4.5,
    },
    "CR005": {
        "specialization": "Food and cooking creator",
        "workflow": "Kitchen shoot, carousel design, short recipe reels",
        "skills": ["food styling", "carousel design", "reels", "social media"],
        "tools": ["Canva", "CapCut", "Firefly"],
        "formats": ["1:1", "4:5", "9:16"],
        "turnaround_days": 3, "commercial_license": True,
        "verified_tools": ["Firefly"], "verified_past_work": False, "rating": 4.3,
    },
    "CR006": {
        "specialization": "Comedy sketch creator",
        "workflow": "Script a skit, film, edit with trending audio",
        "skills": ["comedy", "scriptwriting", "short form video", "trend content"],
        "tools": ["CapCut", "Kling"],
        "formats": ["9:16"],
        "turnaround_days": 2, "commercial_license": True,
        "verified_tools": [], "verified_past_work": False, "rating": 4.1,
    },
}


# Sample portfolio, workflow and verification data for each creator.
PROFILE_EXTRA = {
    "CR001": {
        "verified_workflow": True,
        "process_evidence": "Shared shoot footage, CapCut project files and edit timeline.",
        "portfolio": [
            {"title": "Monsoon Lookbook Reel", "type": "reel", "tools": ["CapCut", "Midjourney"], "description": "AI backgrounds with real styling shots."},
            {"title": "Capsule Wardrobe Carousel", "type": "carousel", "tools": ["Canva"], "description": "Seven-slide outfit guide."},
        ],
    },
    "CR002": {
        "verified_workflow": True,
        "process_evidence": "Drone logs, raw clips and Premiere Pro project screenshots.",
        "portfolio": [
            {"title": "Himalayan Tech Setup", "type": "video", "tools": ["Premiere Pro", "Runway"], "description": "Travel film with AI-extended shots."},
            {"title": "Backcountry Gear Test", "type": "video", "tools": ["DaVinci Resolve"], "description": "Cinematic gear review."},
        ],
    },
    "CR003": {
        "verified_workflow": False,
        "process_evidence": None,
        "portfolio": [
            {"title": "30-Day Strength Routine", "type": "tutorial", "tools": ["CapCut"], "description": "Step-by-step workout series."},
        ],
    },
    "CR004": {
        "verified_workflow": True,
        "process_evidence": "Screen recordings of the full AI tool workflow.",
        "portfolio": [
            {"title": "AI Tools Desk Setup", "type": "tutorial", "tools": ["Runway", "ElevenLabs"], "description": "Walkthrough with AI voiceover."},
            {"title": "Software Suite Deep Dive", "type": "video", "tools": ["Premiere Pro"], "description": "Long-form product review."},
        ],
    },
    "CR005": {
        "verified_workflow": False,
        "process_evidence": None,
        "portfolio": [
            {"title": "15-Minute Meals Carousel", "type": "carousel", "tools": ["Canva", "Firefly"], "description": "Quick recipe cards."},
        ],
    },
    "CR006": {
        "verified_workflow": False,
        "process_evidence": None,
        "portfolio": [
            {"title": "Office Skit Series", "type": "reel", "tools": ["CapCut"], "description": "Relatable workplace comedy."},
        ],
    },
}


def read_default_creators():
    """Read the DEFAULT_CREATORS list from frontend/app.py without running the app."""
    tree = ast.parse(APP_FILE.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "DEFAULT_CREATORS":
                    return ast.literal_eval(node.value)
    raise SystemExit("Could not find DEFAULT_CREATORS in frontend/app.py")


def main():
    url = os.getenv("SUPABASE_URL")
    secret = os.getenv("SUPABASE_SECRET_KEY")
    if not url or not secret:
        raise SystemExit("Missing SUPABASE_URL or SUPABASE_SECRET_KEY in .env")

    rows = []
    for creator in read_default_creators():
        row = {k: v for k, v in creator.items() if k in COLUMNS}
        row.update(EXTRA.get(creator["id"], {}))
        row.update(PROFILE_EXTRA.get(creator["id"], {}))
        rows.append(row)

    client = create_client(url, secret)
    client.table("creators").upsert(rows, on_conflict="id").execute()
    print(f"Done! Uploaded {len(rows)} creators to Supabase.")


if __name__ == "__main__":
    main()