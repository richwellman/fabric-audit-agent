"""Collects tenant metadata via the Power BI / Fabric admin scanner APIs.

Flow (all read-only):
  GetModifiedWorkspaces -> PostWorkspaceInfo -> poll GetScanStatus -> GetScanResult
plus the widelySharedArtifacts endpoints for public/org-wide exposure.

Auth is delegated by default, via DefaultAzureCredential (your `az login`
session, or whatever other credential source is available in the
environment) — your Entra account needs the tenant admin API permissions
used by the scanner (e.g. Fabric/Power BI admin role). For unattended/CI
runs, pass client_id/client_secret to authenticate as a service principal
instead; see README for the tenant settings that permission requires.
"""

import time

import requests
from azure.core.exceptions import ClientAuthenticationError
from azure.identity import ClientSecretCredential, DefaultAzureCredential

SCOPE = "https://analysis.windows.net/powerbi/api/.default"
BASE = "https://api.powerbi.com/v1.0/myorg/admin"

# Scanner API limits (per Microsoft docs): max 100 workspaces per getInfo
# call; polling interval per the scan status guidance.
GETINFO_BATCH = 100
POLL_SECONDS = 15
POLL_TIMEOUT_SECONDS = 30 * 60


class Collector:
    def __init__(
        self,
        tenant_id: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
    ):
        if client_id and client_secret:
            if not tenant_id:
                raise ValueError("TENANT_ID is required when using a service principal")
            self._credential = ClientSecretCredential(
                tenant_id=tenant_id, client_id=client_id, client_secret=client_secret
            )
        else:
            self._credential = DefaultAzureCredential(tenant_id=tenant_id)

    def _token(self) -> str:
        try:
            return self._credential.get_token(SCOPE).token
        except ClientAuthenticationError as e:
            raise RuntimeError(f"Auth failed: {e}") from e

    def _get(self, path: str, params: dict | None = None) -> dict | list:
        resp = requests.get(
            f"{BASE}/{path}",
            headers={"Authorization": f"Bearer {self._token()}"},
            params=params,
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, params: dict, body: dict) -> dict:
        resp = requests.post(
            f"{BASE}/{path}",
            headers={"Authorization": f"Bearer {self._token()}"},
            params=params,
            json=body,
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()

    def workspace_ids(self) -> list[str]:
        """All non-personal, active workspace IDs in the tenant."""
        data = self._get(
            "workspaces/modified",
            params={
                "excludePersonalWorkspaces": "true",
                "excludeInActiveWorkspaces": "true",
            },
        )
        return [w["id"] for w in data]

    def scan(self, workspace_ids: list[str]) -> list[dict]:
        """Run the scanner flow over all workspaces; returns workspace metadata dicts."""
        results: list[dict] = []
        for i in range(0, len(workspace_ids), GETINFO_BATCH):
            batch = workspace_ids[i : i + GETINFO_BATCH]
            scan = self._post(
                "workspaces/getInfo",
                params={
                    "lineage": "True",
                    "datasourceDetails": "True",
                    "getArtifactUsers": "True",
                },
                body={"workspaces": batch},
            )
            scan_id = scan["id"]
            self._wait(scan_id)
            result = self._get(f"workspaces/scanResult/{scan_id}")
            results.extend(result.get("workspaces", []))
        return results

    def _wait(self, scan_id: str) -> None:
        deadline = time.monotonic() + POLL_TIMEOUT_SECONDS
        while time.monotonic() < deadline:
            status = self._get(f"workspaces/scanStatus/{scan_id}")
            if status.get("status") == "Succeeded":
                return
            time.sleep(POLL_SECONDS)
        raise TimeoutError(f"Scan {scan_id} did not complete in time")

    def published_to_web(self) -> list[dict]:
        data = self._get("widelySharedArtifacts/publishedToWeb")
        return data.get("ArtifactAccessEntities", data.get("artifactAccessEntities", []))

    def links_shared_to_whole_org(self) -> list[dict]:
        data = self._get("widelySharedArtifacts/linksSharedToWholeOrganization")
        return data.get("ArtifactAccessEntities", data.get("artifactAccessEntities", []))
