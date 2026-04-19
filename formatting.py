from __future__ import annotations

from savant import MatchupSummary


def format_summary(summary: MatchupSummary) -> str:
    seq = " | ".join(summary.last_results)
    avg = f"{summary.hit_rate:.3f}".lstrip("0")
    breakdown = ", ".join(
        f"{count}x {label}" for label, count in summary.hit_breakdown.items() if count > 0
    ) or "No hits"
    return (
        f"{summary.batter_name} vs {summary.pitcher_name}\n"
        f"{summary.hits} H in {summary.ab} AB ({avg})\n"
        f"Hit breakdown: {breakdown}\n"
        f"Last {summary.last_ab_count} AB: {seq}"
    )


def format_game_block(game_label: str, summaries: list[MatchupSummary]) -> str:
    lines = [f"## {game_label}"]
    for summary in summaries:
        lines.append(format_summary(summary))
        lines.append("")
    return "\n".join(lines).strip()


def format_discord_message(run_date: str, blocks: list[str]) -> list[str]:
    header = f"⚾ Hits matchup bot — {run_date}"
    chunks: list[str] = []
    current = header
    for block in blocks:
        candidate = f"{current}\n\n{block}" if current else block
        if len(candidate) > 1800:
            chunks.append(current)
            current = block
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks
