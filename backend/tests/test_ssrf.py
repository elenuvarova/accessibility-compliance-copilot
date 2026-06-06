"""Security regression: the SSRF validator (_assert_url_safe).

These must stay offline. Reject cases use literal IPs / non-http schemes so the
validator short-circuits before any DNS lookup. The single allow case uses a
literal PUBLIC IP, which also avoids DNS (the bare-IP branch returns early).
"""

import pytest
from fastapi import HTTPException

import main


def _is_rejected(url: str) -> bool:
    try:
        main._assert_url_safe(url)
        return False
    except HTTPException as exc:
        # SSRF rejections are surfaced as 400 to the client.
        assert exc.status_code == 400
        return True


class TestAssertUrlSafeRejects:
    @pytest.mark.parametrize(
        "url",
        [
            "http://169.254.169.254/latest/meta-data/",  # AWS/cloud metadata
            "http://localhost/",                          # loopback hostname
            "http://127.0.0.1/",                          # loopback literal
            "http://10.0.0.5/admin",                      # RFC1918 10.x
            "http://192.168.1.1/",                        # RFC1918 192.168.x
            "http://172.16.0.1/",                         # RFC1918 172.16.x
            "http://[::1]/",                              # IPv6 loopback
            "file:///etc/passwd",                         # non-http scheme
            "gopher://evil/",                             # non-http scheme
            "ftp://host/",                                # non-http scheme
            "http://0.0.0.0/",                            # unspecified
            "",                                           # empty
            "http://",                                    # missing host
        ],
    )
    def test_rejects_dangerous_url(self, url):
        assert _is_rejected(url) is True


class TestAssertUrlSafeAllows:
    def test_allows_public_ip_literal_https(self):
        # 93.184.216.34 is example.com's documented public address. As a bare IP
        # literal the validator returns without resolving DNS -> no network.
        main._assert_url_safe("https://93.184.216.34/")  # must NOT raise

    def test_allows_public_ip_literal_http(self):
        main._assert_url_safe("http://93.184.216.34/some/path?q=1")  # must NOT raise

    def test_loopback_literal_is_not_accidentally_allowed(self):
        # Belt-and-suspenders: confirm the public-IP allow path didn't loosen
        # the loopback check.
        assert _is_rejected("http://127.0.0.1:8000/") is True
