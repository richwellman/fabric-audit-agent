# Phase 2 — MCP demo script (15-minute prospect demo)

Claude Code is the MCP host; the Fabric Core Remote MCP server is the data
plane. The demo's spine is the **contrast between the two modes**: the
static collector produces the scheduled, complete, deterministic report —
then the MCP agent does the things a script structurally can't. Each side
covers the other's blind spot, and the demo shows both blind spots on
purpose.

## The contrast this demo sells

| | Static scanner (phase 1) | MCP agent (phase 2) |
|---|---|---|
| Data plane | Admin scanner APIs (tenant-wide) | Fabric Core MCP tools (per-workspace) |
| Coverage | **Everything**: RBAC + labels + publishedToWeb + endorsement | RBAC/roles/items only — no label or exposure metadata |
| Freshness | Snapshot at scan time | Live state at question time |
| Questions it can answer | The 10 coded rules, nothing else | Any question expressible in English |
| New question turnaround | Write code, redeploy | Ask it (seconds) |
| Follow-up / drill-down | Re-run whole scan | Interactive: pull one thread across workspaces |
| Remediation | Impossible — read-only by design | Possible (role change/removal), human-approved per call |
| Judgment | Hard thresholds (`MAX_ADMINS=3`) | Contextual ("4 admins on a sandbox is fine; on Finance it isn't") |
| Repeatability | Deterministic, schedulable, same answer twice | Conversational, non-deterministic |
| Audit trail | Script logs | Fabric audit log records every call under the signed-in identity |

**What the MCP agent makes possible that the script is limited by** — the
four beats to actually demo:

1. **Investigation, not just detection.** The report says *"guest X has a
   role in workspace Y."* The script stops there — its output is frozen at
   whatever the rules computed. The agent can keep pulling the thread:
   what else does this guest touch, who granted it, what's in that
   workspace, is it capacity-backed?
2. **Unanticipated questions.** Any question outside the 10 coded rules
   costs a dev cycle in the script. The agent answers it in the meeting.
3. **Remediation is reachable.** The script can never fix anything (by
   design). The agent has `update_workspace_role`/`delete_workspace_role`
   one approved click away — shown but declined on screen.
4. **Judgment over thresholds.** The script flags >3 admins everywhere.
   The agent can reason about *which* of those flags matter.

And the honest reverse edge (say it out loud, it builds trust): the MCP
tools **cannot see** sensitivity labels, published-to-web, or endorsement —
only the scanner APIs return that. That's why the deliverable is the
scheduled collector, and the agent is the investigation layer on top.

## Part 0 — Wiring the MCP into Claude Code (one-time, ~10 min, do the day before)

1. **Register the server** (from any directory; `--scope user` makes it
   available in every project):

   ```bash
   claude mcp add --transport http --scope user fabric https://api.fabric.microsoft.com/v1/mcp/core
   ```

2. **Authenticate.** Start an interactive session (`claude`), run `/mcp`,
   select **fabric**, and complete the browser OAuth flow signed in as the
   trial tenant's admin account (Entra ID; the server uses scope
   `https://api.fabric.microsoft.com/.default`). No app registration —
   delegated OAuth, same identity model as the collector's default path.

3. **Verify.** In the same session, prompt:

   > List all my Fabric workspaces

   Expect the trial tenant's workspaces back via the `list_workspaces` tool.
   If it fails: `/mcp` → reauthenticate; needs at least Viewer on one
   workspace (the admin account has far more).

4. **Safety check.** The Core MCP server is not read-only — it exposes
   `delete_workspace`, `add_workspace_role`, etc. Run the demo in Claude
   Code's **default permission mode** (never bypass/auto-accept) so any
   mutating tool call prompts before executing. The demo prompts below are
   all read-only.

Notes:
- The server is **in preview**; tool names/behavior may shift. Re-verify the
  connection the morning of the demo.
- Role-assignment results return principal IDs, not emails. Optionally add
  the [Microsoft Graph MCP server](https://learn.microsoft.com/graph/mcp-server/get-started)
  for email/group resolution; not required — the seeded guest's UPN
  (`#EXT#`) is visible without it.

## Part 0.5 — Tenant prep (reuse from first-run checklist)

- [ ] Seeded violations exist and are known in advance (see
  [first-run-checklist.md](first-run-checklist.md) / next-steps §2): a guest
  (B2B) user with a workspace role, a workspace with 4+ admins, an unlabeled
  semantic model, an org-wide share link.
- [ ] Phase-1 collector has been run **the same morning**:
  `.venv/bin/python -m src.main` → have
  `output/audit-report-<date>.md` open in a second tab/pane.
- [ ] Start Claude Code **from this repo's root** so the agent can read
  [audit-rules.md](audit-rules.md) — the prompts below reference it.
- [ ] Dry-run the full prompt sequence once; note which workspace names the
  seeded findings live in.

## Part 1 — The demo (15 min)

Structure: **report first, then agent** — establish the static scanner as
the baseline deliverable, then let every MCP beat be something the report
visibly could not do.

### 0:00–2:00 — Framing (no tools yet)

Talking track:
- "Purview tells you what data is labeled and what's shared publicly. It
  does **not** tell you who holds what role in which Fabric workspace —
  no user-level or artifact-level access rights." (Backed by the
  practitioner thread cited in [audit-rules.md](audit-rules.md) §vs. Purview.)
- "I'll show you two halves: a scheduled scanner that produces this
  morning's full-tenant findings report, and an AI agent on Fabric's own
  MCP endpoint that can *investigate* those findings live. Watch what each
  one can do that the other can't."

### 2:00–5:00 — The static scanner: the baseline

Show `output/audit-report-<date>.md` (this morning's run). Walk it fast:

- Findings by severity; point at one from each family — the RBAC-01 guest,
  the LBL-01 unlabeled model, the EXP-02 org-wide link.
- Sell its structural strengths: **complete** (every workspace, not
  Purview DSPM's top-100 sample), **deterministic** (same answer twice,
  schedulable nightly, diffable over time), **read-only** (safe to run
  unattended).
- Then plant the limitation, verbatim: *"This report is a snapshot, and it
  only answers the ten questions we coded. Watch what happens when you ask
  the eleventh."*

### 5:00–11:00 — The MCP agent: everything the script can't do

This is the contrast section — four beats, each mapped to a limitation of
the script. Pick the RBAC-01 guest finding from the report as the thread.

**Beat 1 — Investigation (the script's output is frozen; the agent pulls
the thread).** Prompt:

> The audit report flagged guest user <UPN> holding a role in workspace
> <name>. Investigate: check every workspace for role assignments held by
> this user, tell me what role they hold in each, and what items are in
> those workspaces.

The agent chains `list_workspaces` → `list_workspace_roles` →
`list_items` live. Talking track: "To make the script answer this,
someone writes code and redeploys. The agent just did it — against
**live** state, not this morning's snapshot."

**Beat 2 — The unanticipated question (invite one from the audience).**
Have a backup ready if nobody bites:

> Which workspaces have exactly one Admin, and is that admin the same
> person anywhere else? That's a bus-factor problem, not just a rule.

Talking track: "That question is in no rule set. It cost nothing to ask."

**Beat 3 — Judgment over thresholds.** Prompt:

> Read docs/audit-rules.md. The report flagged workspace <name> for having
> 4 admins (RBAC-02). Given what's actually in that workspace and who the
> admins are, how much does this finding matter?

Talking track: "The script flags >3 admins everywhere, unconditionally.
The agent can rank which flags deserve the meeting."

**Beat 4 — Remediation is reachable (shown, declined).** Prompt:

> What would it take to remove the guest user's access? Don't do it.

The agent describes `delete_workspace_role`; if it attempts the call, the
permission prompt appears — **decline it on screen**. Talking track: "The
script can never fix anything, by design. The agent is one approved click
from remediation — and that approval gate is the governance posture."

### 11:00–13:00 — The honest reverse edge: what MCP can't see

Prompt:

> Do the Fabric MCP tools you have expose sensitivity labels,
> published-to-web status, or endorsement for these items?

The agent says no — `list_items`/`get_item` carry no label or
widely-shared metadata. Land the architecture point:

- "That data only comes from the tenant-level **admin scanner APIs** —
  which is exactly why the deliverable is the scheduled collector, and the
  agent is the investigation layer on top. Two data planes, one rule set:
  the script for complete/repeatable, the agent for live/interactive."
- Flip back to the report's LBL-01/EXP-02 findings to close the loop.

### 13:00–14:00 — Positioning and close

- "Why not just Purview?" — answer honestly per
  [audit-rules.md](audit-rules.md): label coverage and public-link exposure
  *are* native; the RBAC enumeration you watched is not.
- Deliverable framing: scheduled read-only scans + prioritized findings
  report; the agent for triage and follow-up; remediation as the follow-on
  engagement.

### 14:00–15:00 — Q&A buffer / fallback slack

## Fallbacks

| Failure | Recovery |
|---|---|
| OAuth/401 mid-demo | `/mcp` → reauthenticate (browser flow, ~30s). Narrate it: "short-lived tokens, by design." |
| "Invalid workspace ID" | Have the agent run `list_workspaces` first and use UUIDs (known preview quirk). |
| MCP endpoint down / tools changed (preview) | Full fallback: walk the collector report only — it contains every finding class including RBAC. The live portion is theater; the report is the deliverable. |
| Agent misses a seeded finding | Ask directly: "Who has roles in workspace <name>? Any guest accounts?" |

## Prep checklist (morning of)

- [ ] `claude` → `/mcp` shows **fabric: connected**; "List all my Fabric workspaces" works.
- [ ] Fresh collector run; report open in second pane.
- [ ] Seeded findings confirmed present in that report; guest UPN and the
  flagged workspace names copied somewhere handy (the Part-1 prompts need
  them verbatim).
- [ ] Session started from repo root; permission mode is default (not auto-accept).
- [ ] Screen: Claude Code left, report right; notifications off.
- [ ] Recording (Loom) armed — this run doubles as the demo recording per next-steps §4.

## Appendix — question bank (for Q&A and improv)

Everything here stays inside what the Core MCP tools can answer
(workspaces, role assignments, items, folders, capacities, catalog
search) except the boundary probes, which are marked — the agent saying
"I can't see that" is itself a demo beat.

### Inventory / warm-up (fast, reliable openers)

> List all my Fabric workspaces with a count. Which ones are on a capacity?

> Search the catalog for anything with "finance" or "HR" in the name —
> what workspaces do those items live in?

> Which workspaces contain lakehouses or warehouses?

(That last one finds where the *data* lives, vs. just reports — which is
where access matters most.)

### RBAC audit (the coded rules, done live)

> For every workspace, list the role assignments. Flag any principal
> whose UPN contains #EXT# — those are guests.

> Which workspaces have more than 3 admins? Which have zero?

> Are there any service principals holding Admin or Member anywhere?

> Which workspaces grant roles to more than 10 individual users instead
> of a group?

### Investigation (pick one finding, pull the thread)

> That guest — check every workspace for their role assignments. What
> role do they hold in each, and what items are in those workspaces?

> For the workspaces where the guest has access, are any of them
> capacity-backed production workspaces vs. sandboxes?

> Is anyone who has Admin on the <name> workspace also an Admin
> somewhere else?

### Unanticipated / judgment (nothing in any rule set)

> Which workspaces have exactly one Admin, and is that same person the
> sole admin anywhere else? Rank the bus-factor risk.

> Read docs/audit-rules.md, then tell me which of the RBAC-02 flags
> actually matter, given what's in each flagged workspace.

> If I could only fix three access problems in this tenant this week,
> which three, and why?

> Do any workspaces look abandoned — no meaningful items, or a sole
> admin who appears nowhere else in the tenant?

### Remediation tease (shown, declined on screen)

> What would it take to remove the guest's access from all three
> workspaces? Don't do it.

> Draft the exact role changes you'd make to fix the admin-sprawl
> finding, as a proposal I could send to the workspace owner.

### Boundary probes (expected answer: no — pivot to the collector)

> Do your tools expose sensitivity labels, published-to-web status, or
> endorsement for these items?

> Can you tell me *when* the guest was granted access, or who granted it?

(The second is audit-log territory — segue to "that's v2, activity-log
correlation," per [audit-rules.md](audit-rules.md) out-of-scope list.)

### Improv cautions

- Without the Graph MCP server, prompts phrased around emails or group
  membership ("is the Marketing group in here?") can stall on
  principal-ID resolution — keep audience-facing prompts workspace- and
  role-centric.
- Dry-run the judgment questions especially: most impressive when they
  land, most variable in output.
