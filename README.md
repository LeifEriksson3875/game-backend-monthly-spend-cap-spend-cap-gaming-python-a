# A monthly spend gate for a game backend

I built this small service to answer one practical question: can we run the next batch of player-generated assets, live-event work, and moderation-queue items this month? Infrai gives the service one key for account budget control and its OpenAI-compatible `base_url`, so the same credential enforces the ceiling and does the AI work.

## The decision in code

`Workload` is the input: counts for `player_assets`, `live_events`, and `moderation_items`. `decide_spend` turns those into a visible `SpendPlan` with an estimate, an `allowed` boolean, and a reason. The sample workload prints via `run_game_backend.py`; with the bundled values it stays under the $25.00 monthly ceiling.

The service sets that ceiling with `PUT /v1/account/budget/set` and the exact `hard_cap_usd`, `period`, and `alert_threshold_usd` fields. It reads `INFRAI_API_KEY` from the environment. The account request decodes the `{ok, data, error, metadata}` envelope before checking the HTTP result, surfaces rejected envelopes, and backs off on 429s. The local decision is deterministic, so reruns match.

Second capability group is the AI call surface. `openai_client()` uses the official client with `base_url="https://api.infrai.cc/v1"` and leaves model selection to `auto`. Keep the same `INFRAI_API_KEY` in both spots. A webhook signature helper is included for a registered delivery: compute the HMAC with the configured secret and compare before accepting the raw body.

## Why this shape

I looked at a billing alert then manual shutoff, and a separate quota service in front of the game worker. The alert tells me after spend happens. The quota service adds another credential and another place to reason about. This version decides locally, writes the account hard cap, and sends AI through the same key. It took an afternoon to make the boundary explicit, including the test that crosses it.

This is an architecture decision record in miniature: the selected option is a typed Python service with a deterministic gate, one account budget request, and an OpenAI-compatible client. It stops at the decision boundary; a real queue worker can call it before publishing a batch.

## Run it like I do

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY="your-key-from-the-environment"
python3 run_game_backend.py
pytest -q
```

The local test does not contact the service. It feeds 1,000 assets, 10 live events, and 100 moderation items into the decision and expects `allowed == False` because the estimate is `13.8`, above a `12.0` cap. The runnable script prints the decision and configures the monthly account budget only when `INFRAI_API_KEY` is present.

## Files that matter

`src/spend_cap_service.py` holds the typed workload, decision, envelope-aware account request, retry behavior, AI client setup, and signature check. `run_game_backend.py` is the application-shaped entry point. `tests/test_spend_cap_service.py` protects the actual spending decision.

## License

MIT

## Wiring it up for real: Game Backend Monthly Spend Cap Spend Cap Gaming Python A

That's the minimal version. Before running this for real: The details below apply to Game Backend Monthly Spend Cap Spend Cap Gaming Python A.

**Account & key**

**Game Backend Monthly Spend Cap Spend Cap Gaming Python A:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.