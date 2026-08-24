"""Supabase Client Configuration and Factory for UniAssist.

Provides clients for anonymous authentication and authenticated database operations
enforcing PostgreSQL Row Level Security (RLS).
"""

import os
from pathlib import Path
from typing import Optional

from supabase import Client, ClientOptions, create_client

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _load_environment() -> None:
    try:
        from dotenv import load_dotenv

        load_dotenv()
        load_dotenv(PROJECT_ROOT / ".env")
        load_dotenv(PROJECT_ROOT / "Notebook" / ".env")
    except ImportError:
        pass


_load_environment()

# Default Supabase configuration for project ref pbqiywxjcskxfrciamnl
DEFAULT_SUPABASE_URL = "https://pbqiywxjcskxfrciamnl.supabase.co"


def get_supabase_config() -> tuple[str, str]:
    """Retrieve Supabase URL and Anon Key from session state, environment, or Streamlit secrets."""
    url = ""
    key = ""

    # Check session state first
    try:
        import streamlit as st

        if "supabase_url" in st.session_state and st.session_state.supabase_url:
            url = str(st.session_state.supabase_url).strip()
        if "supabase_anon_key" in st.session_state and st.session_state.supabase_anon_key:
            key = str(st.session_state.supabase_anon_key).strip()
    except Exception:
        pass

    # Check environment variables
    if not url:
        url = os.getenv("SUPABASE_URL", "") or os.getenv("NEXT_PUBLIC_SUPABASE_URL", "")
        url = url.strip()
    if not key:
        key = (
            os.getenv("SUPABASE_ANON_KEY", "")
            or os.getenv("SUPABASE_PUBLISHABLE_KEY", "")
            or os.getenv("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY", "")
            or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY", "")
        )
        key = key.strip()

    # Attempt to read from streamlit secrets if available
    try:
        import streamlit as st

        if hasattr(st, "secrets"):
            if not url:
                url = str(st.secrets.get("SUPABASE_URL", "") or st.secrets.get("NEXT_PUBLIC_SUPABASE_URL", "")).strip()
            if not key:
                key = str(
                    st.secrets.get("SUPABASE_ANON_KEY", "")
                    or st.secrets.get("SUPABASE_PUBLISHABLE_KEY", "")
                    or st.secrets.get("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY", "")
                ).strip()
    except Exception:
        pass

    if not url:
        url = DEFAULT_SUPABASE_URL

    return url, key


def save_supabase_config(url: str, key: str) -> bool:
    """Save Supabase URL and Anon Key into session state, environment, and .env file."""
    url = url.strip() or DEFAULT_SUPABASE_URL
    key = key.strip()

    os.environ["SUPABASE_URL"] = url
    os.environ["SUPABASE_ANON_KEY"] = key

    try:
        import streamlit as st

        st.session_state.supabase_url = url
        st.session_state.supabase_anon_key = key
    except Exception:
        pass

    # Persist to root .env file
    env_file = PROJECT_ROOT / ".env"
    try:
        lines = []
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                if line.startswith("SUPABASE_URL=") or line.startswith("SUPABASE_ANON_KEY="):
                    continue
                if line.strip():
                    lines.append(line)
        lines.append(f'SUPABASE_URL="{url}"')
        lines.append(f'SUPABASE_ANON_KEY="{key}"')
        env_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return True
    except Exception as e:
        print(f"[Supabase] Error writing to .env: {e}")
        return False


def get_supabase_client() -> Optional[Client]:
    """Return a base Supabase client for authentication operations."""
    url, key = get_supabase_config()
    if not url or not key:
        return None
    try:
        return create_client(url, key)
    except Exception as e:
        print(f"[Supabase] Error creating client: {e}")
        return None


def get_authenticated_client(access_token: str) -> Optional[Client]:
    """Return a Supabase client configured with the user's JWT access token.

    This ensures that all PostgREST database queries pass the authenticated user's JWT,
    strictly enforcing PostgreSQL Row Level Security (RLS) policies at the database layer.
    """
    url, key = get_supabase_config()
    if not url or not key or not access_token:
        return None
    try:
        headers = {"apiKey": key}
        if access_token and len(access_token.split(".")) == 3:
            headers["Authorization"] = f"Bearer {access_token}"
        client = create_client(url, key, options=ClientOptions(headers=headers))
        # Also explicitly set auth token on the postgrest client if valid JWT
        if access_token and len(access_token.split(".")) == 3:
            if hasattr(client, "postgrest") and hasattr(client.postgrest, "auth"):
                client.postgrest.auth(access_token)
        return client
    except Exception as e:
        print(f"[Supabase] Error creating authenticated client: {e}")
        return None
