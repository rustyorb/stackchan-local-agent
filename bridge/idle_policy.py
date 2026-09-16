"""Silence-idle policy shared with the pinned Xiaozhi patch."""


def idle_enabled(value) -> bool:
    return value is not None and int(value) > 0


def watchdog_seconds(value) -> int | None:
    return int(value) + 60 if idle_enabled(value) else None
