"""
gas-delta.py — Compare forge gas snapshots and generate a PR comment.

Usage:
    python tools/gas-delta.py .gas-snapshot-base .gas-snapshot-pr

Output:
    Prints a markdown-formatted gas delta table.
    Exits with code 0 (gas regressions warn but do not block merge).

Called by .github/workflows/contract-ci.yml. The markdown output
is posted as a PR comment via the GitHub Actions API.
"""

import sys
from pathlib import Path

WARN_THRESHOLD_PERCENT = 10.0


def parse_snapshot(path: Path) -> dict[str, int]:
    """Parse a forge .gas-snapshot file into function-gas pairs.

    Each line in a snapshot file has the format:
        FunctionName(args) (gas: 12345)

    Args:
        path: Path to the snapshot file.

    Returns:
        Dict mapping function signature to gas value.
    """
    entries: dict[str, int] = {}

    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or "(gas:" not in line:
                continue

            # Split at "(gas: " to separate function name from gas value
            parts = line.rsplit("(gas: ", 1)
            if len(parts) != 2:
                continue

            func_name = parts[0].strip()
            gas_str = parts[1].rstrip(")")
            try:
                entries[func_name] = int(gas_str)
            except ValueError:
                continue

    return entries


def compute_deltas(
    base: dict[str, int], pr: dict[str, int]
) -> list[dict]:
    """Compute gas deltas between base and PR snapshots.

    Args:
        base: Function-gas pairs from the base branch.
        pr: Function-gas pairs from the PR branch.

    Returns:
        List of delta dicts with keys: function, base_gas, pr_gas,
        delta, percent_change, warning.
    """
    all_functions = sorted(set(base.keys()) | set(pr.keys()))
    deltas = []

    for func in all_functions:
        base_gas = base.get(func)
        pr_gas = pr.get(func)

        if base_gas is None:
            # New function in PR
            deltas.append({
                "function": func,
                "base_gas": "—",
                "pr_gas": pr_gas,
                "delta": "new",
                "percent_change": "new",
                "warning": False,
            })
            continue

        if pr_gas is None:
            # Function removed in PR
            deltas.append({
                "function": func,
                "base_gas": base_gas,
                "pr_gas": "—",
                "delta": "removed",
                "percent_change": "removed",
                "warning": False,
            })
            continue

        delta = pr_gas - base_gas
        percent = (delta / base_gas) * 100 if base_gas > 0 else 0.0
        warning = percent > WARN_THRESHOLD_PERCENT

        deltas.append({
            "function": func,
            "base_gas": base_gas,
            "pr_gas": pr_gas,
            "delta": delta,
            "percent_change": round(percent, 1),
            "warning": warning,
        })

    return deltas


def format_delta_table(deltas: list[dict]) -> str:
    """Format gas deltas as a markdown table for PR comment.

    Args:
        deltas: List of delta dicts from compute_deltas.

    Returns:
        Markdown table string.
    """
    lines = [
        "| Function | Base Gas | PR Gas | Delta | Change % |",
        "|----------|---------|--------|-------|----------|",
    ]

    for d in deltas:
        func = f"`{d['function']}`"

        if d["delta"] == "new":
            lines.append(f"| {func} | — | {d['pr_gas']:,} | 🆕 new | new |")
            continue

        if d["delta"] == "removed":
            lines.append(f"| {func} | {d['base_gas']:,} | — | 🗑️ removed | removed |")
            continue

        base_str = f"{d['base_gas']:,}"
        pr_str = f"{d['pr_gas']:,}"
        delta_val = d["delta"]
        percent = d["percent_change"]

        # Format sign and color indicator
        if delta_val > 0:
            delta_str = f"+{delta_val:,}"
            pct_str = f"+{percent}%"
            if d["warning"]:
                pct_str += " ⚠️"
        elif delta_val < 0:
            delta_str = f"{delta_val:,}"
            pct_str = f"{percent}%"
        else:
            delta_str = "0"
            pct_str = "0.0%"

        lines.append(f"| {func} | {base_str} | {pr_str} | {delta_str} | {pct_str} |")

    return "\n".join(lines) + "\n"


def format_summary(deltas: list[dict]) -> str:
    """Generate summary line for the PR comment.

    Args:
        deltas: List of delta dicts.

    Returns:
        Summary string.
    """
    decreased = sum(
        1 for d in deltas
        if isinstance(d["delta"], int) and d["delta"] < 0
    )
    increased_warn = sum(1 for d in deltas if d["warning"])
    increased_ok = sum(
        1 for d in deltas
        if isinstance(d["delta"], int) and d["delta"] > 0 and not d["warning"]
    )
    unchanged = sum(
        1 for d in deltas
        if isinstance(d["delta"], int) and d["delta"] == 0
    )
    new = sum(1 for d in deltas if d["delta"] == "new")
    removed = sum(1 for d in deltas if d["delta"] == "removed")

    parts = []
    if decreased:
        parts.append(f"{decreased} decreased")
    if increased_ok:
        parts.append(f"{increased_ok} increased (< {WARN_THRESHOLD_PERCENT}%)")
    if increased_warn:
        parts.append(f"{increased_warn} increased > {WARN_THRESHOLD_PERCENT}% ⚠️")
    if unchanged:
        parts.append(f"{unchanged} unchanged")
    if new:
        parts.append(f"{new} new")
    if removed:
        parts.append(f"{removed} removed")

    return ", ".join(parts) + "."


def generate_pr_comment(deltas: list[dict]) -> str:
    """Generate the full gas report PR comment.

    Args:
        deltas: List of delta dicts.

    Returns:
        Complete markdown string.
    """
    warn_count = sum(1 for d in deltas if d["warning"])
    badge = "🟢 **NO REGRESSIONS**" if warn_count == 0 else f"🟡 **{warn_count} WARNING(S)**"

    parts = [
        f"## ⛽ Gas Report {badge}\n",
        format_delta_table(deltas),
        f"\n**Summary:** {format_summary(deltas)}\n",
    ]

    return "\n".join(parts)


def main() -> int:
    """Entry point. Reads two snapshot files, prints PR comment.

    Returns:
        Always 0 (gas regressions warn, never block).
    """
    if len(sys.argv) != 3:
        print(
            f"Usage: {sys.argv[0]} <base-snapshot> <pr-snapshot>",
            file=sys.stderr,
        )
        return 2

    base_path = Path(sys.argv[1])
    pr_path = Path(sys.argv[2])

    for path in [base_path, pr_path]:
        if not path.exists():
            print(f"Error: {path} not found.", file=sys.stderr)
            return 2

    base = parse_snapshot(base_path)
    pr = parse_snapshot(pr_path)
    deltas = compute_deltas(base, pr)
    comment = generate_pr_comment(deltas)
    print(comment)

    return 0


if __name__ == "__main__":
    sys.exit(main())
