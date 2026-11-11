"""Prices are read-only, fail-soft, and never invented.

The picker is gone because a model that could not be chosen did real damage. A
*price* is different: it changes nothing about a run, and a user who is cost-aware
deserves to see it before committing. So the rule this file pins is: a price is
either published by the catalogue or absent. Never estimated from a table we made
up, and never able to block a run.
"""

import pytest

from upfront import prices


SAMPLE = {
    "data": [
        {"id": "nous/flash", "pricing": {"prompt": "0.0000001", "completion": "0.0000004"},
         "architecture": {"output_modalities": ["text"]}},
        {"id": "meituan/longcat-2.5:free", "pricing": {"prompt": "0", "completion": "0"},
         "architecture": {"output_modalities": ["text"]}},
        {"id": "nous/embed-1", "pricing": {"prompt": "0.00000001", "completion": "0"},
         "architecture": {"output_modalities": ["embeddings"]}},
        {"id": "nous/vision", "pricing": {"prompt": "0.0000002", "completion": "0.0000008"},
         "architecture": {"output_modalities": ["text", "image"]}},
    ]
}


def test_prices_are_per_million_tokens():
    table = prices.parse_catalogue(SAMPLE)
    assert table["nous/flash"]["prompt_per_m"] == pytest.approx(0.1)
    assert table["nous/flash"]["completion_per_m"] == pytest.approx(0.4)
    assert table["nous/flash"]["free"] is False


def test_a_zero_priced_model_is_free():
    assert prices.parse_catalogue(SAMPLE)["meituan/longcat-2.5:free"]["free"] is True


def test_embedding_endpoints_are_not_priced_for_a_review():
    table = prices.parse_catalogue(SAMPLE)
    assert "nous/embed-1" not in table
    assert "nous/vision" in table          # text AND image is still a chat model


def test_the_estimate_is_arithmetic_over_published_prices(monkeypatch):
    monkeypatch.setattr(prices, "catalogue", lambda force=False: prices.parse_catalogue(SAMPLE))
    # 100k in at $0.10/M = $0.01 ; 10k out at $0.40/M = $0.004
    assert prices.estimate_cost("nous/flash", 100_000, 10_000) == pytest.approx(0.014)


def test_an_unknown_model_has_no_price_rather_than_a_guess(monkeypatch):
    monkeypatch.setattr(prices, "catalogue", lambda force=False: prices.parse_catalogue(SAMPLE))
    assert prices.price_for("someone/else's-model") is None
    assert prices.estimate_cost("someone/else's-model", 100_000, 10_000) is None


def test_a_session_slug_is_matched_without_its_suffix(monkeypatch):
    """A session reports `:free` / `:latest`; the catalogue may list the bare id."""
    monkeypatch.setattr(prices, "catalogue", lambda force=False: prices.parse_catalogue(SAMPLE))
    assert prices.price_for("nous/flash:latest") is not None


def test_an_offline_catalogue_returns_nothing_and_raises_nothing(monkeypatch):
    def boom(*_a, **_k):
        raise OSError("no network")

    monkeypatch.setattr(prices, "_read_cache", lambda: {"fetched_at": 0, "models": {}})
    monkeypatch.setattr(prices, "_fetch", boom)
    assert prices.catalogue() == {}
    assert prices.estimate_cost("nous/flash", 1000, 100) is None


def test_real_usage_accumulates_and_keeps_the_hosts_cost():
    """The after-run number is the host's own, so it can say 'known'."""
    total = prices.blank_usage()
    prices.add_usage(total, {"prompt_tokens": 1000, "completion_tokens": 200,
                             "total_tokens": 1200, "cost_usd": 0.0021})
    prices.add_usage(total, {"prompt_tokens": 500, "completion_tokens": 100,
                             "total_tokens": 600})
    assert total["calls"] == 2
    assert total["tokens_in"] == 1500
    assert total["tokens_out"] == 300
    assert total["tokens_total"] == 1800
    assert total["cost_usd"] == pytest.approx(0.0021)
    assert total["cost_known"] is True


def test_a_usage_shape_we_do_not_understand_does_not_raise():
    total = prices.blank_usage()
    prices.add_usage(total, object())
    assert total["calls"] == 1
    assert total["tokens_in"] == 0
