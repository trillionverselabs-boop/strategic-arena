from upfront.fetch import _drop_chrome, _clean


def test_github_chrome_is_dropped():
    html = "Skip to content\nSign in\n# Upfront\nA strategic-response review.\nDismiss alert\n"
    out = _drop_chrome(html)
    assert "Skip to content" not in out
    assert "Sign in" not in out
    assert "A strategic-response review." in out


def test_clean_keeps_content_and_caps_noise():
    text = "Title\n\n\n\nBody line\nFooter\n"
    out = _clean(text)
    assert "Body line" in out
    assert "\n\n\n" not in out
