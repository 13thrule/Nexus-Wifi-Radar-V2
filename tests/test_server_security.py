"""
Tests for server security features (rate limiting, authentication).
"""

import pytest
import time
import os

# Import the security classes directly (don't need FastAPI for these tests)
import sys
sys.path.insert(0, str(__file__).rsplit('/', 2)[0])

from nexus.server import RateLimiter, APIKeyAuth


class TestRateLimiter:
    """Tests for the rate limiter."""

    def test_allows_requests_under_limit(self):
        """Test that requests under limit are allowed."""
        limiter = RateLimiter(requests_per_minute=10)
        ip = "192.168.1.1"

        for _ in range(10):
            assert limiter.check_rate_limit(ip) is True
            limiter.record_request(ip)

    def test_blocks_requests_over_limit(self):
        """Test that requests over limit are blocked."""
        limiter = RateLimiter(requests_per_minute=5)
        ip = "192.168.1.1"

        # Make 5 requests (should be allowed)
        for _ in range(5):
            limiter.record_request(ip)

        # 6th request should be blocked
        assert limiter.check_rate_limit(ip) is False

    def test_different_ips_have_separate_limits(self):
        """Test that different IPs have separate limits."""
        limiter = RateLimiter(requests_per_minute=2)

        # IP 1 makes 2 requests
        limiter.record_request("192.168.1.1")
        limiter.record_request("192.168.1.1")

        # IP 1 should be blocked
        assert limiter.check_rate_limit("192.168.1.1") is False

        # IP 2 should still be allowed
        assert limiter.check_rate_limit("192.168.1.2") is True

    def test_scan_cooldown(self):
        """Test scan cooldown functionality."""
        limiter = RateLimiter(scan_cooldown=2)
        ip = "192.168.1.1"

        # First scan should be allowed
        assert limiter.can_scan(ip) is True
        limiter.record_scan(ip)

        # Immediate second scan should be blocked
        assert limiter.can_scan(ip) is False

        # Wait time should be > 0
        assert limiter.get_scan_wait_time(ip) > 0

    def test_scan_cooldown_expires(self):
        """Test that scan cooldown expires."""
        limiter = RateLimiter(scan_cooldown=1)
        ip = "192.168.1.1"

        limiter.record_scan(ip)
        assert limiter.can_scan(ip) is False

        # Wait for cooldown to expire
        time.sleep(1.1)
        assert limiter.can_scan(ip) is True


class TestAPIKeyAuth:
    """Tests for API key authentication."""

    def test_disabled_when_no_env_var(self):
        """Test auth is disabled when NEXUS_API_KEY not set."""
        # Ensure env var is not set
        if "NEXUS_API_KEY" in os.environ:
            del os.environ["NEXUS_API_KEY"]

        auth = APIKeyAuth()
        assert auth.enabled is False

    def test_verify_returns_true_when_disabled(self):
        """Test that verify returns True when auth is disabled."""
        if "NEXUS_API_KEY" in os.environ:
            del os.environ["NEXUS_API_KEY"]

        auth = APIKeyAuth()
        assert auth.verify(None) is True
        assert auth.verify("anything") is True

    def test_enabled_when_env_var_set(self):
        """Test auth is enabled when NEXUS_API_KEY is set."""
        os.environ["NEXUS_API_KEY"] = "test-key-12345"
        try:
            auth = APIKeyAuth()
            assert auth.enabled is True
        finally:
            del os.environ["NEXUS_API_KEY"]

    def test_verify_correct_key(self):
        """Test that correct key passes verification."""
        os.environ["NEXUS_API_KEY"] = "my-secret-key"
        try:
            auth = APIKeyAuth()
            assert auth.verify("my-secret-key") is True
        finally:
            del os.environ["NEXUS_API_KEY"]

    def test_verify_incorrect_key(self):
        """Test that incorrect key fails verification."""
        os.environ["NEXUS_API_KEY"] = "my-secret-key"
        try:
            auth = APIKeyAuth()
            assert auth.verify("wrong-key") is False
            assert auth.verify("") is False
            assert auth.verify(None) is False
        finally:
            del os.environ["NEXUS_API_KEY"]

    def test_generate_key_format(self):
        """Test that generated keys have correct format."""
        key = APIKeyAuth.generate_key()
        # Should be URL-safe base64, ~43 characters for 32 bytes
        assert len(key) >= 40
        assert all(c.isalnum() or c in "-_" for c in key)

    def test_generate_key_uniqueness(self):
        """Test that generated keys are unique."""
        keys = [APIKeyAuth.generate_key() for _ in range(10)]
        assert len(set(keys)) == 10  # All unique
