from ai_search_agent.preflight import check_brightdata_dataset_exists


def test_dataset_format_check():
    # Does not call network; validates simple format logic
    assert check_brightdata_dataset_exists("tok", "gd_123")["ok"] is True
    assert check_brightdata_dataset_exists("tok", "not_gd")["ok"] is False
