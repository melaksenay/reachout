"""Unit tests for TikTokDiscovery helper methods — no browser, no DB."""
from unittest.mock import patch

from app.services.discovery import TikTokDiscovery


@patch.object(TikTokDiscovery, "__init__", lambda self: None)
def _make_scraper() -> TikTokDiscovery:
    scraper = TikTokDiscovery()
    scraper.my_handle = "myhandle"
    return scraper


# --- _parse_followers ---

def test_parse_followers_millions():
    s = _make_scraper()
    assert s._parse_followers("1.2M") == 1_200_000


def test_parse_followers_thousands():
    s = _make_scraper()
    assert s._parse_followers("50K") == 50_000


def test_parse_followers_raw_number():
    s = _make_scraper()
    assert s._parse_followers("1000") == 1000


def test_parse_followers_with_text():
    s = _make_scraper()
    assert s._parse_followers("1.2M followers") == 1_200_000


def test_parse_followers_invalid():
    s = _make_scraper()
    assert s._parse_followers("abc") == 0


# --- _handles_to_profiles ---

def test_handles_to_profiles():
    s = _make_scraper()
    profiles = s._handles_to_profiles(["alice", "bob"])
    assert len(profiles) == 2
    assert profiles[0].handle == "alice"
    assert profiles[0].platform == "tiktok"
    assert profiles[0].url == "https://www.tiktok.com/@alice"
    assert profiles[0].follower_count is None
    assert profiles[1].handle == "bob"


def test_handles_to_profiles_empty():
    s = _make_scraper()
    assert s._handles_to_profiles([]) == []
