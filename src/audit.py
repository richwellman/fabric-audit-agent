"""Applies the audit rule set (docs/audit-rules.md) to scanner output."""

from dataclasses import dataclass

MAX_ADMINS = 3
GROUP_THRESHOLD = 10
LABEL_COVERAGE_MIN = 0.80

LABELED_ITEM_TYPES = ("datasets", "dataflows", "reports", "dashboards")


@dataclass
class Finding:
    rule: str
    severity: str  # HIGH | MEDIUM | LOW
    workspace: str
    detail: str


def run(workspaces: list[dict], published_to_web: list[dict], org_links: list[dict]) -> list[Finding]:
    findings: list[Finding] = []
    for ws in workspaces:
        findings.extend(_rbac(ws))
        findings.extend(_labels(ws))
    findings.extend(_exposure(published_to_web, org_links))
    order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    findings.sort(key=lambda f: (order[f.severity], f.rule))
    return findings


def _users(ws: dict) -> list[dict]:
    return ws.get("users", []) or []


def _rbac(ws: dict) -> list[Finding]:
    findings = []
    name = ws.get("name", ws.get("id", "?"))
    users = _users(ws)

    guests = [u for u in users if "#EXT#" in (u.get("identifier") or "").upper()]
    for g in guests:
        findings.append(Finding(
            "RBAC-01", "HIGH", name,
            f"Guest user {g.get('identifier')} holds role {g.get('groupUserAccessRight')}",
        ))

    admins = [u for u in users if u.get("groupUserAccessRight") == "Admin"]
    if len(admins) > MAX_ADMINS:
        findings.append(Finding(
            "RBAC-02", "MEDIUM", name,
            f"{len(admins)} admins (threshold {MAX_ADMINS}): "
            + ", ".join(a.get("identifier", "?") for a in admins),
        ))
    if users and not admins:
        findings.append(Finding("RBAC-03", "HIGH", name, "Workspace has no Admin"))

    individuals = [u for u in users if u.get("principalType") == "User"]
    if len(individuals) > GROUP_THRESHOLD:
        findings.append(Finding(
            "RBAC-04", "MEDIUM", name,
            f"{len(individuals)} individual user grants; consider security groups",
        ))

    for u in users:
        if u.get("principalType") == "App" and u.get("groupUserAccessRight") in ("Admin", "Member"):
            findings.append(Finding(
                "RBAC-05", "MEDIUM", name,
                f"Service principal {u.get('identifier')} holds {u.get('groupUserAccessRight')}",
            ))
    return findings


def _labels(ws: dict) -> list[Finding]:
    findings = []
    name = ws.get("name", ws.get("id", "?"))
    labeled = 0
    total = 0
    for item_type in LABELED_ITEM_TYPES:
        for item in ws.get(item_type, []) or []:
            total += 1
            if item.get("sensitivityLabel"):
                labeled += 1
            else:
                findings.append(Finding(
                    "LBL-01", "MEDIUM", name,
                    f"{item_type[:-1]} '{item.get('name', item.get('id', '?'))}' has no sensitivity label",
                ))
    if total and labeled / total < LABEL_COVERAGE_MIN:
        findings.append(Finding(
            "LBL-02", "LOW", name,
            f"Label coverage {labeled}/{total} ({labeled / total:.0%}) below {LABEL_COVERAGE_MIN:.0%}",
        ))
    return findings


def _exposure(published_to_web: list[dict], org_links: list[dict]) -> list[Finding]:
    findings = []
    for a in published_to_web:
        findings.append(Finding(
            "EXP-01", "HIGH",
            (a.get("artifactAccessEntity") or a).get("displayName", "?") if isinstance(a, dict) else "?",
            "Report is published to the public web",
        ))
    for a in org_links:
        findings.append(Finding(
            "EXP-02", "MEDIUM",
            (a.get("artifactAccessEntity") or a).get("displayName", "?") if isinstance(a, dict) else "?",
            "Item is link-shared to the entire organization",
        ))
    return findings
