# Next steps

State as of 2026-07-11: phase-1 collector is complete and runnable; machine
setup done (Python 3.12 venv at `.venv/`, Azure CLI installed); first real
run not yet done. See [first-run-checklist.md](first-run-checklist.md) for
the detailed prep steps.

## 1. First real scan (before the trial tenant expires Jul 15)

1. `az login` as the trial tenant's admin account.
2. Trial tenant Fabric admin portal → Tenant settings → enable
   **Enhance admin APIs responses with detailed metadata**.
3. Run: `.venv/bin/python -m src.main`
4. Report lands in `output/audit-report-<date>.md` (gitignored — findings
   stay local, which also means the scan just needs to happen before
   expiry; analysis can follow after).

## 2. Findings tuning (after first scan)

- Sanity-check the report: expect a few true positives, no obvious nonsense.
- Tune thresholds in `src/audit.py` if noisy: `MAX_ADMINS`,
  `GROUP_THRESHOLD`, `LABEL_COVERAGE_MIN`.
- Seed the trial tenant with deliberate violations if the report is too
  clean to be interesting (a guest user, an unlabeled semantic model, an
  org-wide share link) and re-scan.
- Tick "First run against a real tenant" in the README status list.

## 3. Audit write-up

Governance/security framing — an audit report, not a code demo:

- Findings by severity; RBAC / exposure / label-coverage gaps.
- Feature the Purview angle: sensitivity-label coverage is the data-security
  finding most orgs are worst at.
- Include the service-principal caveat: RLS is **not** enforced for SP auth
  on the Power BI Remote MCP endpoint (see README security notes).

## 4. Phase 2 — MCP demo mode

Not started. The scanner currently calls the admin REST APIs directly;
there is no MCP code in the repo yet.

- Same audit narrated live through an MCP-connected agent
  (Fabric Core Remote MCP: `https://api.fabric.microsoft.com/v1/mcp/core`).
- Target: the 15-minute prospect demo path from the README architecture
  section.
- Then: demo recording (Loom).
