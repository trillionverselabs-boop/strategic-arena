from upfront import fetch
from upfront.fetch import _clean, _drop_chrome, _extract_text, _html_to_text, _prose_chars


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


# --- regression: a real Next.js page (nousresearch.com/arete, 1.66 MB)
# put 3,211 SVG path-coordinate tokens in front of every sentence of prose.
# The engine graded a move off a title and a pile of coordinates.


def test_svg_path_data_never_reaches_the_model():
    html = (
        '<div class="nw-research-brand"><svg viewBox="0 0 200 279.662">'
        '<path d="M178.187 0H21.8099C9.76403 0 0 9.76403 0 21.8099V257.852"/>'
        '<path d="M80.4471 13.6696C70.1348 13.6696 61.7787 21.6047 61.7787 51.4664"/>'
        "</svg></div>"
        "<p>We post-trained Qwen3.8-27B to reinforce Western values.</p>"
        "<p>Second real sentence about the eval.</p>"
    )
    out = _html_to_text(html)
    assert "M178.187" not in out
    assert "21.8099" not in out
    assert "61.7787" not in out
    assert "post-trained Qwen3.8-27B" in out
    assert "Second real sentence" in out


def test_body_survives_a_page_larger_than_the_byte_cap():
    """A 1.5 MB page must not be truncated to its <head> before extraction."""
    filler = ('<svg><path d="M0 0L1 1C2 2 3 3Z"/></svg>' * 40_000)
    body = (
        b"<p>We post-trained Alibaba's Qwen3.8-27B to reinforce Western values on a "
        b"Chinese-trained model, and measured what changed with an 803-prompt eval "
        b"across seven value categories. The fact score rose from 2.32 to 2.98 and "
        b"answers containing propaganda fell from 22% to 1%, in line with the Western "
        b"models we tested.</p>"
    )
    payload = filler.encode() + body
    assert len(payload) > 200_000  # the old cap
    text = _extract_text(payload)
    assert text is not None
    assert "reinforce Western values" in text
    assert "803-prompt eval" in text


def test_junk_only_page_is_rejected_not_ingested():
    """No prose means no document — the caller records a failed fetch instead."""
    junk = (
        '<html><head><title>Introducing Arete-27B</title></head><body>'
        '<svg viewBox="0 0 200 279.662"><path d="M178.187 0H21.8099C9.76403 0 0 9.76403"/></svg>'
        "</body></html>"
    ).encode()
    assert _extract_text(junk) is None


def test_prose_chars_ignores_coordinates_and_counts_words():
    assert _prose_chars("M178.187 0H21.8099 9.76403") == 0
    assert _prose_chars("the model removed framing") >= 18


def test_html_entities_are_unescaped():
    """A model reading "Alibaba&#x27;s" is reading markup, not prose."""
    out = _clean(_html_to_text("<p>Alibaba&#x27;s Qwen3.8-27B &amp; the eval</p>"))
    assert "&#x27;" not in out
    assert "Alibaba's Qwen3.8-27B & the eval" in out
