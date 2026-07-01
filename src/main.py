"""Entry point: collect -> audit -> report."""

import os
import pathlib
from datetime import date

from dotenv import load_dotenv

from . import audit, report
from .collector import Collector


def main() -> None:
    load_dotenv()
    collector = Collector(
        tenant_id=os.environ["TENANT_ID"],
        client_id=os.environ["CLIENT_ID"],
        client_secret=os.environ["CLIENT_SECRET"],
    )

    ids = collector.workspace_ids()
    print(f"Scanning {len(ids)} workspaces...")
    workspaces = collector.scan(ids)
    ptw = collector.published_to_web()
    org_links = collector.links_shared_to_whole_org()

    findings = audit.run(workspaces, ptw, org_links)
    out = pathlib.Path("output") / f"audit-report-{date.today().isoformat()}.md"
    out.write_text(report.render(findings, len(workspaces)))
    print(f"Wrote {out} ({len(findings)} findings)")


if __name__ == "__main__":
    main()
