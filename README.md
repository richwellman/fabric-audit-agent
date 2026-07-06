# fabric-audit-agent

Automated security audit of a Microsoft Fabric / Power BI tenant. Scans every workspace via the admin **scanner APIs** and produces a findings report covering workspace RBAC, external/guest access, sensitivity-label coverage, endorsement, service-principal access, and org-wide/public exposure.

Built as a fixed-scope, demoable audit — point it at a tenant as a signed-in Fabric/Power BI admin, get a prioritized findings report back.

## What it checks

See [docs/audit-rules.md](docs/audit-rules.md) for the full rule set. Summary:

| Category | Example findings |
|---|---|
| RBAC | Guest (B2B) users with workspace roles; admin-role sprawl; workspaces with no admin; individual grants where groups should be used |
| External exposure | Reports published to web (public internet); links shared to the entire org |
| Sensitivity labels | Items missing labels; per-workspace label coverage % |
| Service principals | Which SPs hold access where, and at what role |
| Endorsement | Semantic models that are neither certified nor promoted |
| Hygiene | Workspaces inactive beyond a threshold |

## Architecture

Two modes, one data layer:

1. **Deterministic collector (this repo, phase 1)** — Python against the Power BI/Fabric admin REST APIs. Reliable, schedulable, produces the same answer twice. This is the client-deliverable path.
2. **Agent/MCP demo mode (phase 2)** — the same audit narrated live through an MCP-connected agent (Fabric Core Remote MCP at `https://api.fabric.microsoft.com/v1/mcp/core`). This is the 15-minute prospect demo path.

```
Your Azure/Entra sign-in (az login, via DefaultAzureCredential)
        │  — or a service principal (client secret) for unattended runs
        │
        ▼
GetModifiedWorkspaces  ──► workspace ID inventory
        │
        ▼
PostWorkspaceInfo (getArtifactUsers=True, lineage=True, datasourceDetails=True)
        │  (async — poll GetScanStatus until Succeeded)
        ▼
GetScanResult  ──► full metadata: users/roles, labels, endorsement, items
        │
        ├── widelySharedArtifacts/publishedToWeb
        ├── widelySharedArtifacts/linksSharedToWholeOrganization
        ▼
audit.py (rules)  ──►  report.py  ──►  output/audit-report-YYYY-MM-DD.md
```

## Prerequisites (tenant-side setup)

Two auth options — pick one:

**A. Delegated (default, recommended for interactive/ad-hoc runs)**

1. Run `az login` as a user with a **Fabric admin / Power BI admin** role (or Global Admin) in the target tenant. The collector authenticates as *you*, via `DefaultAzureCredential` — no app registration or client secret required.
2. If token acquisition fails with a consent/permission error, the Azure CLI's first-party app may need admin consent for the Power BI Service API in your tenant — a tenant admin can grant this once via the Entra admin center (Enterprise applications → Azure CLI → Permissions).

**B. Service principal (for unattended/CI/scheduled runs)**

1. **Entra app registration**, plus a client secret. The app must have **NO admin-consent-required Power BI permissions** — per Microsoft docs, service-principal auth for read-only admin APIs is mutually exclusive with delegated admin permissions, a common setup failure.
2. Put the app in an **Entra security group**.
3. Fabric admin portal → Tenant settings → **Allow service principals to use read-only admin APIs** → enabled for that security group.
4. Set `TENANT_ID`, `CLIENT_ID`, `CLIENT_SECRET` in `.env`.

Either way, also enable:
- Fabric admin portal → Tenant settings → **Enhance admin APIs responses with detailed metadata** (needed for labels/users detail)

## Running

```bash
pip install -r requirements.txt
az login   # skip if using a service principal (option B above)
cp .env.example .env   # set TENANT_ID / CLIENT_ID / CLIENT_SECRET as needed
python -m src.main
```

Output lands in `output/audit-report-<date>.md`.

## Security notes

- The scan runs **read-only** — the auditor never mutates anything.
- Scan results contain user identities and item names; treat `output/` as confidential and don't commit it (gitignored).
- Delegated auth (default) runs as your own identity, so all API calls are attributable to you and bounded by your own admin permissions — no long-lived secret to manage or leak. Prefer this unless you need unattended/scheduled runs.
- If using a service principal instead: it is **read-only**, and the client secret is a long-lived credential — store it securely (not in `.env` committed to git; it's gitignored here) and rotate it periodically.
- If later exposing this via the Power BI Remote MCP: **RLS is not enforced for service-principal auth** on that endpoint — do not put SP-authenticated query access in front of end users.

## Status

- [x] Repo scaffold, rule set, collector/audit/report skeleton (2026-07-01)
- [ ] First run against a real tenant (needs the Entra app + tenant settings above)
- [ ] Findings tuning after first real scan
- [ ] Phase 2: MCP demo mode
- [ ] Demo recording (Loom) for prospect conversations
