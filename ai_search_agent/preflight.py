import os
from typing import Dict, Optional
import requests


def _bool(val: Optional[str]) -> bool:
    return bool(val and val.strip())


def check_openai(key: Optional[str], timeout: int = 6) -> Dict[str, object]:
    """Lightweight OpenAI key validation using the models endpoint.

    Does not consume completion tokens. Returns dict with ok + message.
    """
    if not _bool(key):
        return {"ok": False, "message": "Missing OpenAI API key"}
    try:
        resp = requests.get(
            "https://api.openai.com/v1/models",
            headers={"Authorization": f"Bearer {key}"},
            timeout=timeout,
        )
        if resp.status_code == 200:
            try:
                data = resp.json()
                ids = {str(m.get("id")) for m in (data.get("data") or []) if isinstance(m, dict)}
                if "gpt-4o" in ids or "gpt-4o-mini" in ids:
                    return {"ok": True, "message": "OpenAI reachable (model available)"}
                return {"ok": True, "message": "OpenAI reachable (model access uncertain)"}
            except Exception:
                return {"ok": True, "message": "OpenAI reachable"}
        return {
            "ok": False,
            "message": f"OpenAI check failed ({resp.status_code})",
        }
    except Exception as e:
        return {"ok": False, "message": f"OpenAI check error: {e}"}


def _bd_get(url: str, token: str, timeout: int):
    return requests.get(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        },
        timeout=timeout,
    )


def check_brightdata_token(token: Optional[str], timeout: int = 8) -> Dict[str, object]:
    if not _bool(token):
        return {"ok": False, "message": "Missing Bright Data token"}
    try:
        # The stable token probe is the legacy list endpoint
        u = "https://api.brightdata.com/datasets/list?page=1"
        resp = _bd_get(u, token, timeout)
        try:
            print(f"   [preflight] Bright Data token check {resp.status_code} @ {u}")
        except Exception:
            pass
        if resp.status_code == 200:
            return {"ok": True, "message": "Bright Data reachable"}
        return {"ok": False, "message": f"Bright Data check failed ({resp.status_code})"}
    except Exception as e:
        return {"ok": False, "message": f"Bright Data check error: {e}"}


def check_brightdata_dataset_exists(token: Optional[str], dataset_id: Optional[str], timeout: int = 10) -> Dict[str, object]:
    if not _bool(token):
        return {"ok": False, "message": "Missing Bright Data token"}
    if not _bool(dataset_id):
        return {"ok": False, "message": "Missing dataset id"}
    # We avoid heavy/triggering API calls; validate format only.
    ds = str(dataset_id)
    if ds.startswith("gd_") and len(ds) >= 6:
        return {"ok": True, "message": "Looks valid (format check)"}
    return {"ok": False, "message": "Dataset id format looks unusual"}


def preflight_check(
    *,
    openai_api_key: Optional[str],
    brightdata_api_key: Optional[str],
    reddit_dataset_id: Optional[str],
    reddit_comments_dataset_id: Optional[str],
) -> Dict[str, object]:
    """Run a suite of preflight checks and print CLI logs.

    Returns a dict with aggregate status and per-check results.
    """
    print("\n🚦 Preflight: starting system checks…")

    results: Dict[str, object] = {}

    r_openai = check_openai(openai_api_key)
    print(f"   🤖 OpenAI: {'OK' if r_openai['ok'] else 'FAIL'} — {r_openai['message']}")
    results["openai"] = r_openai

    r_bright = check_brightdata_token(brightdata_api_key)
    print(f"   🌐 Bright Data API: {'OK' if r_bright['ok'] else 'FAIL'} — {r_bright['message']}")
    results["brightdata_api"] = r_bright

    r_ds_search = check_brightdata_dataset_exists(brightdata_api_key, reddit_dataset_id)
    print(f"   📚 Reddit search dataset: {'OK' if r_ds_search['ok'] else 'FAIL'} — {r_ds_search['message']}")
    results["reddit_dataset"] = r_ds_search

    r_ds_comments = check_brightdata_dataset_exists(brightdata_api_key, reddit_comments_dataset_id)
    print(f"   💬 Reddit comments dataset: {'OK' if r_ds_comments['ok'] else 'FAIL'} — {r_ds_comments['message']}")
    results["reddit_comments_dataset"] = r_ds_comments

    all_ok = all(
        r.get("ok")
        for r in [r_openai, r_bright, r_ds_search, r_ds_comments]
    )
    results["ok"] = all_ok
    print("✅ Preflight: all systems go!\n" if all_ok else "❌ Preflight: issues detected.\n")
    return results
