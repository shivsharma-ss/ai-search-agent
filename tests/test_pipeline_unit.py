from types import SimpleNamespace

import ai_search_agent.pipeline as pipeline


def test_run_research_happy_path(monkeypatch):
    # Stub web operations
    monkeypatch.setattr(
        pipeline, "serp_search", lambda q, engine="google", api_key=None: {"engine": engine, "q": q}
    )
    monkeypatch.setattr(
        pipeline, "reddit_search_api", lambda keyword, api_key=None, dataset_id=None: {"parsed_posts": [{"url": "https://r/test"}]}
    )
    monkeypatch.setattr(
        pipeline, "reddit_post_retrieval", lambda urls, api_key=None, comments_dataset_id=None: {"comments": [{"content": "Nice"}]}
    )

    # Stub LLM calls for analysis steps
    class FakeResp:
        def __init__(self, content):
            self.content = content

    def fake_invoke(messages):
        # For URL analysis structured output
        if isinstance(messages, list) and messages and messages[0].get("role") == "system":
            # Return different text depending on stage to emulate analyses
            return FakeResp("analysis")
        return FakeResp("analysis")

    # For structured output call in analyze_reddit_posts
    class FakeStructured:
        def invoke(self, messages):
            return SimpleNamespace(selected_urls=["https://r/test"]) 

    fake_llm = SimpleNamespace(
        invoke=fake_invoke, with_structured_output=lambda schema: FakeStructured()
    )
    out = pipeline.run_research("test question", llm_override=fake_llm)
    assert out.get("final_answer")
    assert out.get("google_results")["engine"] == "google"
    assert out.get("bing_results")["engine"] == "bing"
    assert out.get("reddit_results")["parsed_posts"]
