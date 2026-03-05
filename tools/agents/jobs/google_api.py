from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from typing import Any

import requests


class GoogleApiError(RuntimeError):
    pass


@dataclass(slots=True)
class GoogleApiClient:
    timeout_sec: int = 30

    def access_token(self) -> str:
        scopes = os.environ.get(
            "GOOGLE_API_SCOPES",
            ",".join(
                [
                    "https://www.googleapis.com/auth/cloud-platform",
                    "https://www.googleapis.com/auth/analytics.readonly",
                    "https://www.googleapis.com/auth/tagmanager.readonly",
                ]
            ),
        )
        commands = [
            [
                "gcloud",
                "auth",
                "application-default",
                "print-access-token",
                f"--scopes={scopes}",
            ],
            ["gcloud", "auth", "application-default", "print-access-token"],
            ["gcloud", "auth", "print-access-token"],
        ]
        last_error = ""
        for cmd in commands:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
            )
            token = proc.stdout.strip()
            if proc.returncode == 0 and token:
                return token
            last_error = proc.stderr.strip() or proc.stdout.strip()

        raise GoogleApiError(
            "Unable to get Google access token. Run:\n"
            "gcloud auth application-default login "
            "--scopes=https://www.googleapis.com/auth/cloud-platform,"
            "https://www.googleapis.com/auth/analytics.readonly,"
            "https://www.googleapis.com/auth/tagmanager.readonly\n"
            f"Details: {last_error}"
        )

    def get_json(self, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        token = self.access_token()
        resp = requests.get(
            url,
            params=params,
            headers={"Authorization": f"Bearer {token}"},
            timeout=self.timeout_sec,
        )
        if resp.status_code >= 400:
            raise GoogleApiError(self._format_error(resp))
        data = resp.json()
        if not isinstance(data, dict):
            raise GoogleApiError(f"Expected JSON object from {url}")
        return data

    def post_json(self, url: str, payload: dict[str, Any]) -> dict[str, Any]:
        token = self.access_token()
        resp = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            data=json.dumps(payload),
            timeout=self.timeout_sec,
        )
        if resp.status_code >= 400:
            raise GoogleApiError(self._format_error(resp))
        data = resp.json()
        if not isinstance(data, dict):
            raise GoogleApiError(f"Expected JSON object from {url}")
        return data

    @staticmethod
    def _format_error(resp: requests.Response) -> str:
        body = resp.text
        try:
            parsed = resp.json()
            body = json.dumps(parsed, ensure_ascii=True)
        except Exception:
            pass
        return f"HTTP {resp.status_code}: {body[:1200]}"
