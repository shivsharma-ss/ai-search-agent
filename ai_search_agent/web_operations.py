import os
from urllib.parse import quote_plus

import requests
from dotenv import load_dotenv

from .snapshot_operations import download_snapshot, poll_snapshot_status

load_dotenv()

dataset_id = "gd_lvz8ah06191smkebj4"


def _make_api_request(url, *, api_key: str | None = None, **kwargs):
    """Helper to POST to Bright Data API with auth and error handling.

    Args:
        api_key: Bright Data API key. Falls back to env if None.
    """
    api_key = api_key or os.getenv("BRIGHTDATA_API_KEY")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(url, headers=headers, **kwargs)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return None
    except Exception as e:
        print(f"Unknown error: {e}")
        return None


def serp_search(query, engine="google", *, api_key: str | None = None):
    """Search via Bright Data SERP and return extracted sections.

    Args:
        query: Search query string.
        engine: Either "google" or "bing".
    Returns:
        Dict with minimal extracted sections or None on failure.
    """
    if engine == "google":
        base_url = "https://www.google.com/search"
    elif engine == "bing":
        base_url = "https://www.bing.com/search"
    else:
        raise ValueError(f"Unknown engine {engine}")

    url = "https://api.brightdata.com/request"

    payload = {
        "zone": "ai_agent",
        "url": f"{base_url}?q={quote_plus(query)}&brd_json=1",
        "format": "raw",
    }

    print(f"🌐 SERP: requesting {engine.title()} results…")
    full_response = _make_api_request(url, json=payload, api_key=api_key)
    if not full_response:
        return None

    extracted_data = {
        "knowledge": full_response.get("knowledge", {}),
        "organic": full_response.get("organic", []),
    }
    try:
        print(
            f"🔎 SERP: got {len(extracted_data['organic'])} organic results from {engine.title()}"
        )
    except Exception:
        pass
    return extracted_data


def _trigger_and_download_snapshot(
    trigger_url, params, data, *, api_key: str | None = None, operation_name="operation"
):
    """Trigger a Bright Data dataset and download its snapshot when ready."""
    print(f"🚚 Triggering Bright Data dataset for {operation_name}…")
    trigger_result = _make_api_request(
        trigger_url, params=params, json=data, api_key=api_key
    )
    if not trigger_result:
        return None

    snapshot_id = trigger_result.get("snapshot_id")
    if not snapshot_id:
        return None

    if not poll_snapshot_status(snapshot_id, api_key=api_key):
        return None

    raw_data = download_snapshot(snapshot_id, api_key=api_key)
    return raw_data


def reddit_search_api(
    keyword,
    date="All time",
    sort_by="Hot",
    num_of_posts=75,
    *,
    api_key: str | None = None,
    dataset_id: str | None = None,
):
    """Search Reddit via Bright Data dataset and return minimal info."""
    if not dataset_id:
        raise ValueError("dataset_id is required for Reddit search")
    if not api_key:
        raise ValueError("api_key is required for Reddit search")

    trigger_url = "https://api.brightdata.com/datasets/v3/trigger"

    params = {
        "dataset_id": dataset_id,
        "include_errors": "true",
        "type": "discover_new",
        "discover_by": "keyword",
    }

    data = [
        {
            "keyword": keyword,
            "date": date,
            "sort_by": sort_by,
            "num_of_posts": num_of_posts,
        }
    ]

    raw_data = _trigger_and_download_snapshot(
        trigger_url, params, data, api_key=api_key, operation_name="reddit"
    )

    if not raw_data:
        return None

    # Debug: Print the data shape only
    print(
        f"DEBUG: raw_data type: {type(raw_data)}; length: {len(raw_data) if isinstance(raw_data, list) else 'n/a'}"
    )

    # Ensure raw_data is a list
    if not isinstance(raw_data, list):
        print(
            f"Warning: Expected list for reddit data, got {type(raw_data)}: {raw_data}"
        )
        return {"parsed_posts": [], "total_found": 0}

    parsed_data = []
    for post in raw_data:
        # Ensure each post is a dictionary
        if not isinstance(post, dict):
            print(f"Warning: Expected dict for post, got {type(post)}: {post}")
            continue

        parsed_post = {
            "title": post.get("title", "No title"),
            "url": post.get("url", "No URL"),
        }
        parsed_data.append(parsed_post)

    return {"parsed_posts": parsed_data, "total_found": len(parsed_data)}


def reddit_post_retrieval(
    urls,
    days_back=10,
    load_all_replies=False,
    comment_limit="",
    *,
    api_key: str | None = None,
    comments_dataset_id: str | None = None,
):
    """Retrieve Reddit post comments given a list of post URLs."""
    if not urls:
        return None
    if not comments_dataset_id:
        raise ValueError(
            "comments_dataset_id is required for Reddit comments retrieval"
        )
    if not api_key:
        raise ValueError("api_key is required for Reddit comments retrieval")

    trigger_url = "https://api.brightdata.com/datasets/v3/trigger"

    params = {"dataset_id": comments_dataset_id, "include_errors": "true"}

    data = [
        {
            "url": url,
            "days_back": days_back,
            "load_all_replies": load_all_replies,
            "comment_limit": comment_limit,
        }
        for url in urls
    ]

    raw_data = _trigger_and_download_snapshot(
        trigger_url, params, data, api_key=api_key, operation_name="reddit comments"
    )
    if not raw_data:
        return None

    # Ensure raw_data is a list
    if not isinstance(raw_data, list):
        print(
            f"Warning: Expected list for reddit comments data, got {type(raw_data)}: {raw_data}"
        )
        return {"comments": [], "total_retrieved": 0}

    parsed_comments = []
    for comment in raw_data:
        # Ensure each comment is a dictionary
        if not isinstance(comment, dict):
            print(f"Warning: Expected dict for comment, got {type(comment)}: {comment}")
            continue

        parsed_comment = {
            "comment_id": comment.get("comment_id", "No ID"),
            "content": comment.get("comment", "No content"),
            "date": comment.get("date_posted", "No date"),
        }
        parsed_comments.append(parsed_comment)

    return {"comments": parsed_comments, "total_retrieved": len(parsed_comments)}
