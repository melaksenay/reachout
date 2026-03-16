import json
from unittest.mock import patch, MagicMock

from app.core.cache import cached, invalidate_cache


class TestCachedDecorator:

    def test_cache_miss_calls_function_and_stores(self):
        mock_redis = MagicMock()
        mock_redis.get.return_value = None

        @cached("test_key", ttl_seconds=30)
        def my_func():
            return {"data": 42}

        with patch("app.core.cache.get_redis", return_value=mock_redis):
            result = my_func()

        assert result == {"data": 42}
        mock_redis.get.assert_called_once_with("cache:test_key")
        mock_redis.setex.assert_called_once()
        args = mock_redis.setex.call_args[0]
        assert args[0] == "cache:test_key"
        assert args[1] == 30
        assert json.loads(args[2]) == {"data": 42}

    def test_cache_hit_returns_cached_value(self):
        mock_redis = MagicMock()
        mock_redis.get.return_value = '{"data": 42}'

        call_count = 0

        @cached("test_key", ttl_seconds=30)
        def my_func():
            nonlocal call_count
            call_count += 1
            return {"data": 99}

        with patch("app.core.cache.get_redis", return_value=mock_redis):
            result = my_func()

        assert result == {"data": 42}
        assert call_count == 0

    def test_redis_get_error_falls_through(self):
        mock_redis = MagicMock()
        mock_redis.get.side_effect = Exception("connection lost")

        @cached("test_key", ttl_seconds=30)
        def my_func():
            return {"data": 42}

        with patch("app.core.cache.get_redis", return_value=mock_redis):
            result = my_func()

        assert result == {"data": 42}

    def test_redis_unavailable_falls_through(self):
        @cached("test_key", ttl_seconds=30)
        def my_func():
            return {"data": 42}

        with patch("app.core.cache.get_redis", return_value=None):
            result = my_func()

        assert result == {"data": 42}

    def test_redis_set_error_still_returns_result(self):
        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        mock_redis.setex.side_effect = Exception("write failed")

        @cached("test_key", ttl_seconds=30)
        def my_func():
            return {"data": 42}

        with patch("app.core.cache.get_redis", return_value=mock_redis):
            result = my_func()

        assert result == {"data": 42}


class TestInvalidateCache:

    def test_invalidate_deletes_keys(self):
        mock_redis = MagicMock()
        with patch("app.core.cache.get_redis", return_value=mock_redis):
            invalidate_cache("dashboard", "tags")
        mock_redis.delete.assert_called_once_with("cache:dashboard", "cache:tags")

    def test_invalidate_no_redis(self):
        with patch("app.core.cache.get_redis", return_value=None):
            invalidate_cache("dashboard")  # should not raise

    def test_invalidate_redis_error(self):
        mock_redis = MagicMock()
        mock_redis.delete.side_effect = Exception("connection lost")
        with patch("app.core.cache.get_redis", return_value=mock_redis):
            invalidate_cache("dashboard")  # should not raise
