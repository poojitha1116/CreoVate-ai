import os

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()


def get_client():
    """Make a Supabase client using the publishable key (read-only)."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        return None
    return create_client(url, key)


def fetch_creators():
    """Get all creators from Supabase. Return [] if anything goes wrong."""
    try:
        client = get_client()
        if client is None:
            return []
        response = client.table("creators").select("*").order("id").execute()
        return response.data or []
    except Exception as error:
        print(f"Could not load creators from Supabase: {error}")
        return []