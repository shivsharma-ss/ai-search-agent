from ai_search_agent import prompts as P


def test_google_analysis_messages_shape():
    msgs = P.get_google_analysis_messages("What is X?", {"organic": []})
    assert isinstance(msgs, list)
    assert len(msgs) == 2
    assert msgs[0]["role"] == "system"
    assert msgs[1]["role"] == "user"


def test_reddit_url_analysis_messages_shape():
    msgs = P.get_reddit_url_analysis_messages("Why Y?", {"parsed_posts": []})
    assert len(msgs) == 2
    assert all("content" in m for m in msgs)

