"""
parse-slither.py — Parse Slither JSON output into a GitHub PR comment.

Usage:
    python tools/parse-slither.py slither-output.json

Output:
    Prints a markdown-formatted findings table grouped by severity.
    Exits with code 1 if any HIGH severity findings exist (blocks PR merge).
    Exits with code 0 otherwise.

This script is called by .github/workflows/contract-ci.yml after
Slither runs. The markdown output is posted as a PR comment via
the GitHub Actions API.
"""

import json
import sys
from pathlib import Path

SEVERITY_ORDER = {"High": 0, "Medium": 1, "Low": 2, "Informational": 3}
SEVERITY_EMOJI = {"High": "🔴", "Medium": "🟡", "Low": "⚪", "Informational": "ℹ️"}


def parse_findings(data: dict) -> list[dict]:
    """Extract findings from Slither JSON output.

    Args:
        data: Parsed JSON from Slither's --json output.

    Returns:
        List of finding dicts with keys: impact, detector, description,
        file, line, confidence.
    """
    findings = []

    if not data.get("results", {}).get("detectors"):
        return findings

    for detector in data["results"]["detectors"]:
        # Extract the first source mapping for file and line
        file_path = "unknown"
        line_number = 0

        elements = detector.get("elements", [])
        if elements:
            source = elements[0].get("source_mapping", {})
            file_path = source.get("filename_relative", "unknown")
            lines = source.get("lines", [])
            line_number = lines[0] if lines else 0

        findings.append({
            "impact": detector.get("impact", "Unknown"),
            "confidence": detector.get("confidence", "Unknown"),
            "detector": detector.get("check", "unknown"),
            "description": detector.get("description", "").split("\n")[0].strip(),
            "file": file_path,
            "line": line_number,
        })

    return findings


def group_by_severity(findings: list[dict]) -> dict[str, list[dict]]:
    """Group findings by severity level.

    Args:
        findings: List of finding dicts from parse_findings.

    Returns:
        Dict mapping severity string to list of findings.
    """
    groups: dict[str, list[dict]] = {}
    for finding in findings:
        severity = finding["impact"]
        if severity not in groups:
            groups[severity] = []
        groups[severity].append(finding)
    return groups


def format_summary_badges(groups: dict[str, list[dict]]) -> str:
    """Generate severity count badges for the PR comment header.

    Args:
        groups: Dict from group_by_severity.

    Returns:
        Markdown string with severity badges.
    """
    badges = []
    for severity in SEVERITY_ORDER:
        count = len(groups.get(severity, []))
        emoji = SEVERITY_EMOJI.get(severity, "")
        badges.append(f"{emoji} **{severity}: {count}**")
    return " | ".join(badges)


def format_findings_table(findings: list[dict]) -> str:
    """Format findings as a markdown table.

    Args:
        findings: List of finding dicts.

    Returns:
        Markdown table string.
    """
    if not findings:
        return "_No findings._\n"

    lines = [
        "| Impact | Detector | File | Line | Description |",
        "|--------|----------|------|------|-------------|",
    ]

    # Sort by severity order
    sorted_findings = sorted(
        findings,
        key=lambda f: SEVERITY_ORDER.get(f["impact"], 99),
    )

    for f in sorted_findings:
        lines.append(
            f"| {f['impact']} | `{f['detector']}` | `{f['file']}` | {f['line']} | {f['description'][:80]} |"
        )

    return "\n".join(lines) + "\n"


def generate_pr_comment(findings: list[dict]) -> str:
    """Generate the full PR comment markdown.

    Args:
        findings: List of finding dicts from parse_findings.

    Returns:
        Complete markdown string for the PR comment.
    """
    groups = group_by_severity(findings)
    high_count = len(groups.get("High", []))

    status_badge = "🔴 **FAIL**" if high_count > 0 else "🟢 **PASS**"

    parts = [
        f"## 🛡️ Slither Security Analysis {status_badge}\n",
        format_summary_badges(groups),
        "\n",
        "### Findings\n",
        format_findings_table(findings),
    ]

    if high_count > 0:
        parts.append(
            f"\n> ⚠️ **{high_count} HIGH severity finding(s) detected. PR merge blocked.**\n"
        )

    return "\n".join(parts)


def main() -> int:
    """Entry point. Reads Slither JSON, prints PR comment, returns exit code.

    Returns:
        0 if no HIGH findings, 1 if HIGH findings exist.
    """
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <slither-output.json>", file=sys.stderr)
        return 2

    input_path = Path(sys.argv[1])
    if not input_path.exists():
        print(f"Error: {input_path} not found.", file=sys.stderr)
        return 2

    with open(input_path) as f:
        data = json.load(f)

    findings = parse_findings(data)
    comment = generate_pr_comment(findings)
    print(comment)

    high_count = len([f for f in findings if f["impact"] == "High"])
    return 1 if high_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
