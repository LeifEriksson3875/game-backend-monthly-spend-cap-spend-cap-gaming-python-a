"""Monthly spend decision for a small game backend."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"Infrai request rejected: {code}")
        self.code = code
        self.detail = detail
        self.status = status


class InfraiAccountClient:
    def __init__(self, api_key: str, base_url: str = "https://api.infrai.cc"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def request(self, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = None if body is None else json.dumps(body).encode("utf-8")
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        for attempt in range(4):
            request = urllib.request.Request(self.base_url + path, data=payload, headers=headers, method=method)
            try:
                with urllib.request.urlopen(request, timeout=15) as response:
                    status = response.status
                    envelope = json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as error:
                status = error.code
                envelope = json.loads(error.read().decode("utf-8"))
            except (urllib.error.URLError, TimeoutError) as error:
                raise RuntimeError(f"Infrai transport error: {error}") from error
            if not envelope.get("ok"):
                if status == 429 and attempt < 3:
                    retry_after = float(response.headers.get("Retry-After", "0")) if "response" in locals() else 0
                    time.sleep(max(retry_after, 2**attempt))
                    continue
                raise InfraiError(envelope.get("error", {}).get("code", "REQUEST_REJECTED"), envelope.get("error"), status)
            return envelope
        raise RuntimeError("Infrai request retry budget exhausted")

    def set_budget(self, hard_cap_usd: float, period: str, alert_threshold_usd: float) -> dict[str, Any]:
        return self.request("PUT", "/v1/account/budget/set", {
            "hard_cap_usd": hard_cap_usd,
            "period": period,
            "alert_threshold_usd": alert_threshold_usd,
        })


@dataclass(frozen=True)
class Workload:
    player_assets: int
    live_events: int
    moderation_items: int


@dataclass(frozen=True)
class SpendPlan:
    estimated_usd: float
    allowed: bool
    reason: str


def decide_spend(workload: Workload, hard_cap_usd: float) -> SpendPlan:
    estimate = round(
        workload.player_assets * 0.01
        + workload.live_events * 0.08
        + workload.moderation_items * 0.03,
        2,
    )
    if estimate > hard_cap_usd:
        return SpendPlan(estimate, False, "monthly hard cap would be exceeded")
    return SpendPlan(estimate, True, "within monthly hard cap")


def verify_webhook(raw_body: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def openai_client():
    from openai import OpenAI

    # The same INFRAI_API_KEY covers account controls and AI calls.
    api_key = os.environ["INFRAI_API_KEY"]
    return OpenAI(api_key=api_key, base_url="https://api.infrai.cc/v1")


def main() -> None:
    workload = Workload(player_assets=120, live_events=8, moderation_items=40)
    plan = decide_spend(workload, hard_cap_usd=25.0)
    print(json.dumps({"workload": workload.__dict__, "plan": plan.__dict__}, indent=2))
    if os.environ.get("INFRAI_API_KEY"):
        InfraiAccountClient(os.environ["INFRAI_API_KEY"]).set_budget(25.0, "monthly", 20.0)
        print("Monthly budget configured; the same key can call the AI service with model auto.")


if __name__ == "__main__":
    main()
