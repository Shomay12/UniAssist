"""Private Chat & Conversation Service for UniAssist.

Enforces user-isolated persistent storage with Supabase PostgreSQL Row Level Security (RLS)
and persistent user-isolated disk storage.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
import re
from typing import Any, Optional
import uuid

from supabase import Client

DATA_DIR = Path(__file__).resolve().parent / "user_data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def _get_user_file(user_id: str) -> Path:
    safe_id = re.sub(r"[^a-zA-Z0-9_-]", "_", str(user_id))
    return DATA_DIR / f"{safe_id}.json"


def _load_user_disk_data(user_id: str) -> dict[str, Any]:
    if not user_id:
        return {"conversations": [], "messages": {}}
    filepath = _get_user_file(user_id)
    if filepath.exists():
        try:
            return json.loads(filepath.read_text(encoding="utf-8"))
        except Exception:
            return {"conversations": [], "messages": {}}
    return {"conversations": [], "messages": {}}


def _save_user_disk_data(user_id: str, data: dict[str, Any]) -> None:
    if not user_id:
        return
    filepath = _get_user_file(user_id)
    try:
        temp_file = filepath.with_suffix(".tmp")
        temp_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        temp_file.replace(filepath)
    except Exception:
        pass


def generate_chat_title(prompt: str) -> str:
    """Generate a clean, concise 3-5 word title from the user's first question."""
    cleaned = prompt.strip()
    prefixes = [
        r"^(can you|could you|please|tell me|explain|what is|what are|how to|how does|why is|why are)\s+",
        r"^(briefly|summarize|give an overview of|describe)\s+",
    ]
    title_candidate = cleaned
    for prefix in prefixes:
        title_candidate = re.sub(prefix, "", title_candidate, flags=re.IGNORECASE)

    title_candidate = re.sub(r"[?!.,;:]+$", "", title_candidate).strip()

    words = title_candidate.split()
    if len(words) > 5:
        title = " ".join(words[:5]) + "..."
    elif words:
        title = " ".join(words)
    else:
        title = "New Study Chat"

    return title.strip().capitalize()


def check_database_schema(client: Client) -> tuple[bool, str]:
    """Check if the required database tables exist in Supabase."""
    if client is None:
        return False, "Supabase client is not initialized."
    try:
        client.table("conversations").select("id").limit(1).execute()
        client.table("messages").select("id").limit(1).execute()
        return True, ""
    except Exception as e:
        err = str(e)
        if "PGRST205" in err or "Could not find the table" in err or "schema cache" in err:
            return False, "Database tables 'conversations' and 'messages' do not exist yet in Supabase."
        return False, err


def get_user_conversations(client: Optional[Client], user_id: Optional[str] = None) -> list[dict[str, Any]]:
    """Fetch all conversations belonging to the authenticated user.

    Combines Supabase PostgreSQL records (RLS) with user-isolated disk persistence.
    """
    remote_convs: list[dict[str, Any]] = []
    if client is not None:
        try:
            response = client.table("conversations").select("*").order("updated_at", desc=True).execute()
            remote_convs = response.data or []
        except Exception:
            remote_convs = []

    if not user_id:
        return remote_convs

    disk_data = _load_user_disk_data(user_id)
    disk_convs = disk_data.get("conversations", [])

    seen_ids = set()
    combined: list[dict[str, Any]] = []

    for conv in remote_convs:
        seen_ids.add(conv["id"])
        combined.append(conv)

    for conv in disk_convs:
        if conv["id"] not in seen_ids:
            seen_ids.add(conv["id"])
            combined.append(conv)

    def sort_key(c: dict[str, Any]) -> str:
        return c.get("updated_at") or c.get("created_at") or ""

    combined.sort(key=sort_key, reverse=True)
    return combined


def group_conversations_by_date(conversations: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Group conversations into time categories: Today, Yesterday, Previous 7 Days, Older."""
    groups: dict[str, list[dict[str, Any]]] = {
        "Today": [],
        "Yesterday": [],
        "Previous 7 Days": [],
        "Older": [],
    }

    now = datetime.now(timezone.utc)
    today_date = now.date()

    for conv in conversations:
        raw_date = conv.get("updated_at") or conv.get("created_at")
        if not raw_date:
            groups["Older"].append(conv)
            continue

        try:
            clean_date_str = str(raw_date).replace("Z", "+00:00")
            dt = datetime.fromisoformat(clean_date_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            conv_date = dt.date()
            delta_days = (today_date - conv_date).days

            if delta_days == 0:
                groups["Today"].append(conv)
            elif delta_days == 1:
                groups["Yesterday"].append(conv)
            elif 2 <= delta_days <= 7:
                groups["Previous 7 Days"].append(conv)
            else:
                groups["Older"].append(conv)
        except Exception:
            groups["Older"].append(conv)

    return {k: v for k, v in groups.items() if v}


def create_conversation(client: Optional[Client], user_id: str, title: str) -> dict[str, Any]:
    """Create a new conversation record for the user.

    Persists to Supabase and user-isolated disk store.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    conv_id = str(uuid.uuid4())
    conv_entry = {
        "id": conv_id,
        "user_id": user_id,
        "title": title or "New Conversation",
        "created_at": now_iso,
        "updated_at": now_iso,
    }

    if client is not None:
        try:
            response = (
                client.table("conversations")
                .insert(
                    {
                        "user_id": user_id,
                        "title": title or "New Conversation",
                    }
                )
                .execute()
            )
            if response.data and len(response.data) > 0:
                conv_entry = response.data[0]
        except Exception:
            pass

    # Save to user-isolated disk store
    disk_data = _load_user_disk_data(user_id)
    disk_data["conversations"].insert(0, conv_entry)
    _save_user_disk_data(user_id, disk_data)

    return conv_entry


def get_conversation_messages(
    client: Optional[Client], conversation_id: str, user_id: Optional[str] = None
) -> list[dict[str, Any]]:
    """Fetch all messages for a specific conversation."""
    if client is not None:
        try:
            response = (
                client.table("messages")
                .select("*")
                .eq("conversation_id", conversation_id)
                .order("created_at", desc=False)
                .execute()
            )
            if response.data:
                return response.data
        except Exception:
            pass

    if user_id:
        disk_data = _load_user_disk_data(user_id)
        return disk_data.get("messages", {}).get(conversation_id, [])

    return []


def save_message(
    client: Optional[Client],
    conversation_id: str,
    user_id: str,
    role: str,
    content: str,
    sources: Optional[list[dict[str, Any]]] = None,
) -> dict[str, Any]:
    """Save a user or assistant message."""
    now_iso = datetime.now(timezone.utc).isoformat()
    msg_id = str(uuid.uuid4())
    msg_entry = {
        "id": msg_id,
        "conversation_id": conversation_id,
        "user_id": user_id,
        "role": role,
        "content": content,
        "sources": sources or [],
        "created_at": now_iso,
    }

    if client is not None:
        try:
            data = {
                "conversation_id": conversation_id,
                "user_id": user_id,
                "role": role,
                "content": content,
                "sources": sources or [],
            }
            response = client.table("messages").insert(data).execute()
            if response.data and len(response.data) > 0:
                msg_entry = response.data[0]
            try:
                client.table("conversations").update({"updated_at": "now()"}).eq("id", conversation_id).execute()
            except Exception:
                pass
        except Exception:
            pass

    # Save to user-isolated disk store
    disk_data = _load_user_disk_data(user_id)
    if "messages" not in disk_data:
        disk_data["messages"] = {}
    if conversation_id not in disk_data["messages"]:
        disk_data["messages"][conversation_id] = []
    disk_data["messages"][conversation_id].append(msg_entry)

    # Update conversation updated_at in disk store
    for c in disk_data.get("conversations", []):
        if c["id"] == conversation_id:
            c["updated_at"] = now_iso

    _save_user_disk_data(user_id, disk_data)
    return msg_entry


def rename_conversation(
    client: Optional[Client], conversation_id: str, new_title: str, user_id: Optional[str] = None
) -> bool:
    """Rename a conversation."""
    if not conversation_id or not new_title.strip():
        return False

    if client is not None:
        try:
            client.table("conversations").update({"title": new_title.strip(), "updated_at": "now()"}).eq(
                "id", conversation_id
            ).execute()
        except Exception:
            pass

    if user_id:
        disk_data = _load_user_disk_data(user_id)
        for c in disk_data.get("conversations", []):
            if c["id"] == conversation_id:
                c["title"] = new_title.strip()
                c["updated_at"] = datetime.now(timezone.utc).isoformat()
        _save_user_disk_data(user_id, disk_data)

    return True


def delete_conversation(client: Optional[Client], conversation_id: str, user_id: Optional[str] = None) -> bool:
    """Delete a conversation."""
    if not conversation_id:
        return False

    if client is not None:
        try:
            client.table("conversations").delete().eq("id", conversation_id).execute()
        except Exception:
            pass

    if user_id:
        disk_data = _load_user_disk_data(user_id)
        disk_data["conversations"] = [c for c in disk_data.get("conversations", []) if c["id"] != conversation_id]
        if "messages" in disk_data and conversation_id in disk_data["messages"]:
            disk_data["messages"].pop(conversation_id, None)
        _save_user_disk_data(user_id, disk_data)

    return True
