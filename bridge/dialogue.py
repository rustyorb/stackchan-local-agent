"""Portable dialogue shaping for the optional bridge relay."""

ALLOWED_ROLES = {"system", "user", "assistant"}


def bounded_dialogue(dialogue, max_messages=24):
    """Return one system message plus the most recent portable turns.

    Xiaozhi remains the history owner. This function only bounds the copy
    forwarded for a request; it never stores or reconstructs history.
    """
    clean = [
        {"role": m["role"], "content": str(m["content"])}
        for m in dialogue
        if isinstance(m, dict)
        and m.get("role") in ALLOWED_ROLES
        and str(m.get("content", "")).strip()
    ]
    systems = [m for m in clean if m["role"] == "system"]
    turns = [m for m in clean if m["role"] != "system"]
    keep_system = systems[:1]
    room = max(0, max_messages - len(keep_system))
    return keep_system + turns[-room:] if room else keep_system
