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

1. Run `az login` as a user with a **Fabric admin / Power BI admin** role (or Global Admin) in the target tenant. The collector authenticates as *you*, via `DefaultAzureCredential` — no app registration or client secret required.
2. Fabric admin portal → Tenant settings:
   - **Enhance admin APIs responses with detailed metadata** → enabled (needed for labels/users detail)
3. If token acquisition fails with a consent/permission error, the Azure CLI's first-party app may need admin consent for the Power BI Service API in your tenant — a tenant admin can grant this once via the Entra admin center (Enterprise applications → Azure CLI → Permissions).

## Running

```bash
pip install -r requirements.txt
az login
cp .env.example .env   # optional: set TENANT_ID if az login has access to more than one tenant
python -m src.main
```

Output lands in `output/audit-report-<date>.md`.

## Security notes

- The scan runs **read-only** — the auditor never mutates anything.
- Scan results contain user identities and item names; treat `output/` as confidential and don't commit it (gitignored).
- Auth is delegated (your own identity, via `DefaultAzureCredential`), so all API calls are attributable to you and bounded by your own admin permissions — no long-lived secret to manage or leak.

## Status

- [x] Repo scaffold, rule set, collector/audit/report skeleton (2026-07-01)
- [ ] First run against a real tenant (needs the Entra app + tenant settings above)
- [ ] Findings tuning after first real scan
- [ ] Phase 2: MCP demo mode
- [ ] Demo recording (Loom) for prospect conversations
