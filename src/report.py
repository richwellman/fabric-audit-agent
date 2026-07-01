"""Renders findings into the markdown audit report."""

from collections import Counter
from datetime import date

from .audit import Finding


def render(findings: list[Finding], workspace_count: int) -> str:
    counts = Counter(f.severity for f in findings)
    lines = [
        f"# Fabric tenant security audit — {date.today().isoformat()}",
        "",
        f"Workspaces scanned: **{workspace_count}** · Findings: "
        f"**{counts.get('HIGH', 0)} high**, {counts.get('MEDIUM', 0)} medium, "
        f"{counts.get('LOW', 0)} low",
        "",
    ]
    for severity in ("HIGH", "MEDIUM", "LOW"):
        group = [f for f in findings if f.severity == severity]
        if not group:
            continue
        lines.append(f"## {severity} ({len(group)})")
        lines.append("")
        lines.append("| Rule | Workspace / item | Finding |")
        lines.append("|------|------------------|---------|")
        for f in group:
            lines.append(f"| {f.rule} | {f.workspace} | {f.detail} |")
        lines.append("")
    lines.append("---")
    lines.append("*Read-only audit. Rule definitions: docs/audit-rules.md.*")
    return "\n".join(lines)
