"""The address guard: a URL the model chose must not reach a non-public host.

`arena_run` takes URLs from the model (the `urls` field in tools.py), and the
fetched text comes back into the run — so without this guard a prompt-injected
page could make the plugin read a LAN host or the cloud-metadata endpoint and
hand the contents to the model. These tests pin the guard behaviourally.
"""

import urllib.request

import pytest

from upfront import fetch


def test_non_public_targets_are_refused():
    for url in (
        "http://127.0.0.1/",
        "http://127.0.0.1:8080/admin",
        "http://localhost/",
        "http://10.0.0.8/",
        "http://172.16.4.4/",
        "http://192.168.1.1/",
        "http://169.254.169.254/latest/meta-data/",   # cloud metadata
        "http://100.64.0.1/",                          # CGNAT
        "http://0.0.0.0/",
        "http://[::1]/",
        "http://[fd00::1]/",                            # IPv6 ULA
        "http://[fe80::1]/",                            # IPv6 link-local
        "file:///etc/passwd",
        "ftp://example.com/x",
        "http://",
    ):
        assert fetch._url_is_public(url) is False, url


def test_a_global_address_is_allowed():
    assert fetch._url_is_public("http://8.8.8.8/") is True


def test_a_global_ipv6_address_is_allowed():
    import socket
    try:
        socket.getaddrinfo("2606:2800:220:1::1", None)
    except OSError:
        pytest.skip("this environment cannot resolve IPv6 literals")
    assert fetch._url_is_public("https://[2606:2800:220:1::1]/") is True


def test_a_name_that_resolves_into_the_lan_is_refused(monkeypatch):
    """A public-looking hostname that resolves to a LAN address is still refused."""
    monkeypatch.setattr(fetch.socket, "getaddrinfo",
                        lambda host, port: [(2, 1, 6, "", ("192.168.1.10", 0))])
    assert fetch._url_is_public("http://internal.example.com/") is False


def test_one_private_address_among_many_is_refused(monkeypatch):
    monkeypatch.setattr(fetch.socket, "getaddrinfo",
                        lambda host, port: [(2, 1, 6, "", ("8.8.8.8", 0)),
                                            (2, 1, 6, "", ("10.0.0.5", 0))])
    assert fetch._url_is_public("http://mixed.example.com/") is False


def test_fetch_url_refuses_a_private_address_without_any_request():
    fetch.LAST_SKIPPED.clear()
    assert fetch.fetch_url("http://169.254.169.254/latest/meta-data/") is None
    assert fetch.LAST_SKIPPED, "a refused link must be recorded, not dropped"
    assert "169.254.169.254" in fetch.LAST_SKIPPED[0][0]
    assert "refused" in fetch.LAST_SKIPPED[0][1]


def test_a_redirect_to_a_private_address_is_refused():
    handler = fetch._PublicRedirectHandler()
    req = urllib.request.Request("http://8.8.8.8/")
    with pytest.raises(fetch._Refused):
        handler.redirect_request(req, None, 302, "Found", {},
                                 "http://169.254.169.254/latest/meta-data/")


def test_a_redirect_to_a_public_address_is_followed():
    handler = fetch._PublicRedirectHandler()
    req = urllib.request.Request("http://8.8.8.8/")
    new = handler.redirect_request(req, None, 302, "Found", {}, "http://8.8.8.8/x")
    assert isinstance(new, urllib.request.Request)
