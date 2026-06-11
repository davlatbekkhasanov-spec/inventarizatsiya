from __future__ import annotations


def fmt_stopwatch(seconds: float) -> str:
    s = max(0, int(seconds))
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{sec:02d}"
    return f"{m:02d}:{sec:02d}"


def progress_bar(percent: float, *, width: int = 10, positive: bool = True) -> str:
    pct = max(0.0, min(100.0, percent))
    filled = int(round(pct / 100 * width))
    if positive:
        fill, empty = "🟩", "⬜"
    else:
        fill, empty = "🟥", "⬜"
    return fill * filled + empty * (width - filled)


def clock_box(clock: str) -> str:
    return f"<code>⏱ {clock}</code>"
