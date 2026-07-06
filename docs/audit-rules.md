# Audit rule set

The rules are the product — the collector just feeds them. Each rule has an ID, severity, what it flags, and why a client should care. Severities: **HIGH** (real exposure, act now), **MEDIUM** (governance gap, plan remediation), **LOW** (hygiene).

## RBAC

| ID | Severity | Rule | Why it matters |
|----|----------|------|----------------|
| RBAC-01 | HIGH | Guest (B2B) user holds any workspace role (UPN contains `#EXT#`) | External identity inside the tenant's data estate; HIPAA/compliance exposure if PHI-adjacent |
| RBAC-02 | MEDIUM | Workspace has more than 3 Admins | Admin sprawl defeats least-privilege; admins can delete the workspace and change access |
| RBAC-03 | HIGH | Workspace has zero Admins | Orphaned workspace — nobody owns access decisions |
| RBAC-04 | MEDIUM | Individual user grants where >10 individuals share the same role in one workspace | Should be a security group; individual grants rot as people move |
| RBAC-05 | MEDIUM | Service principal holds Admin or Member (not Viewer/Contributor) | Automation identities rarely need admin; broad SP access is a lateral-movement risk |

## External exposure

| ID | Severity | Rule | Why it matters |
|----|----------|------|----------------|
| EXP-01 | HIGH | Report published to web (`publishedToWeb`) | Public internet exposure — anyone with the URL, no auth |
| EXP-02 | MEDIUM | Item shared via link to the whole organization | Every employee incl. future hires; usually broader than intended |

## Sensitivity labels

| ID | Severity | Rule | Why it matters |
|----|----------|------|----------------|
| LBL-01 | MEDIUM | Semantic model / lakehouse / warehouse with no sensitivity label | Unlabeled data can't be governed by DLP; Purview policies don't apply |
| LBL-02 | LOW | Workspace label coverage below 80% | Signals labeling isn't operationalized in that team |

## Endorsement / trust

| ID | Severity | Rule | Why it matters |
|----|----------|------|----------------|
| END-01 | LOW | Semantic model neither certified nor promoted, but consumed by reports in other workspaces | Cross-workspace dependency on unvetted data |

## Hygiene

| ID | Severity | Rule | Why it matters |
|----|----------|------|----------------|
| HYG-01 | LOW | Workspace on Premium/Fabric capacity with no modifications in 90+ days | Paying capacity for a dead workspace; also a stale-access surface |

## Deliberately out of scope (v1)

- Item-level permissions inside a workspace (scanner API returns workspace-level users; item-level needs per-item calls — v2)
- Activity-log correlation (who actually *used* the access) — v2, requires activity events API
- OneLake shortcut review to external sources (S3/ADLS) — v2, needs Fabric item detail APIs
- Auto-remediation of any kind — this tool is read-only by design; remediation is the consulting conversation

## Tuning knobs

Thresholds live in `src/audit.py` as constants: `MAX_ADMINS=3`, `GROUP_THRESHOLD=10`, `LABEL_COVERAGE_MIN=0.80`, `STALE_DAYS=90`. First real scan will tell us whether these defaults are sane.

## vs. Microsoft Purview

Checked what Purview and the Fabric admin portal already cover before building this, so the tool fills real gaps rather than reinventing shipped functionality (researched 2026-07-06, Microsoft Learn).

**Genuine gaps — no native Purview/Fabric report covers these:**
- **RBAC-05** (service principal holds Admin/Member) — no dedicated report anywhere correlates SPN identity to Fabric workspace role. Entra logs show SPN *authentication*, not Fabric *authorization*.
- **RBAC-02/03/04** (admin sprawl, zero-admin, individual-grant sprawl) — Purview DSPM's Fabric risk assessment only samples the top 100 workspaces by usage, weekly, with no per-item/per-principal role detail. Full tenant enumeration still needs the scanner APIs directly.
- **RBAC-01** (guest holds a workspace role) — Entra Access Reviews handle guest lifecycle generically; DSPM flags "accessible externally" at the workspace level. Neither maps a specific guest to a specific Fabric workspace and role.

**Overlaps with native functionality — kept anyway for a single unified report, not because Microsoft left a gap:**
- **LBL-01/LBL-02** (sensitivity label coverage) — Purview Information Protection Posture Reports and Fabric's own protection metrics report already do this natively. This is the one rule set that's a genuine duplicate.
- **EXP-01/EXP-02** (published to web, org-wide link) — same `WidelySharedArtifacts` endpoints DSPM and the Fabric admin portal's Content sharing report already surface. Included here for one combined findings report, not because the data was otherwise unavailable.

**Not modeled by Purview either way:** END-01 (endorsement/certification) and HYG-01 (stale workspace) are Fabric-specific concepts outside Purview's scope.

**Positioning:** if asked "why not just use Purview for this" — the honest answer is most of it, for label coverage and public-link exposure. The reason this tool exists is the RBAC rules Purview doesn't cover at all (service principals, full admin/individual-grant enumeration, guest-to-workspace correlation) — that's the actual gap, and the rest rides along for a single report.

Independently confirmed by a live practitioner thread, not just docs: [Fabric community — "How can I audit Fabric authorization rights (Purview)?"](https://community.fabric.microsoft.com/t5/Fabric-platform/How-can-i-audit-fabric-autohrisation-rights-Purview/m-p/4783600#M19215). Both replies agree Purview "doesn't currently show user-level or artifact-level access rights in Fabric," and the accepted answer — stitch together the Fabric/Power BI admin portal, the Power BI REST/Graph APIs, and audit logs yourself — is exactly the pattern this tool automates. The original poster called the gap "really a missed opportunity," which is a useful line for framing why this exists.
