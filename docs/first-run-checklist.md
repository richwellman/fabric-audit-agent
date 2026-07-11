# First real run — checklist

Machine + tenant prep for the first scan (target: trial tenant, before the
July 15 trial expiry). All steps are one-time except the last two.

## Machine (this Mac, as of 2026-07-11)

- [ ] **Python 3.10+** — the code uses `str | None` type hints and will crash
  on import under 3.9. Check: `python3 --version`. If too old:
  `brew install python@3.12` (or use `uv`/pyenv if preferred).
- [ ] **Azure CLI** — not installed (checked 2026-07-11). Needed for the
  default delegated auth path (`az login` → `DefaultAzureCredential`).
  Install: `brew install azure-cli`.
- [ ] **Dependencies** — from the repo root:
  `pip3 install -r requirements.txt`
  (azure-identity, requests, python-dotenv)

## Tenant (one-time, in the trial tenant's admin portals)

- [ ] Signed-in account has a **Fabric admin / Power BI admin** role in the
  target tenant (delegated auth runs as you — no app registration needed).
- [ ] Fabric admin portal → Tenant settings →
  **Enhance admin APIs responses with detailed metadata** = enabled.
  Without this, the scan comes back without sensitivity labels and user
  detail, and most of the rule set has nothing to check.
- [ ] If `az login` token acquisition fails with a consent error: Entra admin
  center → Enterprise applications → **Azure CLI** → grant admin consent for
  the Power BI Service API (one-time; see README "Prerequisites" option A).

## Run

- [ ] `az login` — pick the trial tenant if prompted (or set `TENANT_ID` in
  `.env`, copied from `.env.example`, to pin it).
- [ ] From the repo root: `python3 -m src.main`
- [ ] Report lands in `output/audit-report-<date>.md`. `output/` is
  gitignored — findings contain user identities and item names; treat as
  confidential.

## After the run

- [ ] Sanity-check findings against the tenant (a couple of true positives,
  no obvious nonsense) — then tune thresholds in `src/audit.py`
  (`MAX_ADMINS`, `GROUP_THRESHOLD`, `LABEL_COVERAGE_MIN`) if needed.
- [ ] Write up results, governance/security framing — audit findings,
  RBAC/exposure/label gaps (the project plan's Jul 20 deliverable).
- [ ] Tick "First run against a real tenant" in README Status.

## Known code state

- 2026-07-11: fixed missing `output/` directory creation in `src/main.py`
  (would have thrown `FileNotFoundError` on the very first run) — not yet
  committed/pushed.
