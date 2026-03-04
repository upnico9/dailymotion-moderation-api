import time

from infrastructure.cache import VideoCache


class TestVideoCache:

    def _sample_data(self) -> dict:
        return {
            "title": "Test Video",
            "channel": "news",
            "owner": "user123",
            "filmstrip_60_url": "https://example.com/filmstrip.jpg",
            "embed_url": "https://example.com/embed/123",
        }

    def test_set_and_get(self):
        cache = VideoCache(default_ttl=300, max_size=1000)
        data = self._sample_data()

        cache.set("video_1", data)
        result = cache.get("video_1")

        assert result == data

    def test_get_expired(self):
        cache = VideoCache(default_ttl=300, max_size=1000)
        data = self._sample_data()

        cache.set("video_1", data, ttl=0)
        time.sleep(0.01)
        result = cache.get("video_1")

        assert result is None

    def test_get_expired_with_frozen_time(self, frozen_time):
        cache = VideoCache(default_ttl=60, max_size=1000, time_func=frozen_time)
        data = self._sample_data()

        cache.set("video_1", data)

        frozen_time.advance(59)
        assert cache.get("video_1") == data

        frozen_time.advance(2)
        assert cache.get("video_1") is None

    def test_get_missing(self):
        cache = VideoCache(default_ttl=300, max_size=1000)

        result = cache.get("nonexistent")

        assert result is None

    def test_invalidate(self):
        cache = VideoCache(default_ttl=300, max_size=1000)
        data = self._sample_data()

        cache.set("video_1", data)
        cache.invalidate("video_1")
        result = cache.get("video_1")

        assert result is None

    def test_invalidate_nonexistent(self):
        cache = VideoCache(default_ttl=300, max_size=1000)

        cache.invalidate("nonexistent")

    def test_clear(self):
        cache = VideoCache(default_ttl=300, max_size=1000)
        data = self._sample_data()

        cache.set("video_1", data)
        cache.set("video_2", data)
        cache.set("video_3", data)

        cache.clear()

        assert cache.get("video_1") is None
        assert cache.get("video_2") is None
        assert cache.get("video_3") is None

    def test_custom_ttl_per_entry(self, frozen_time):
        cache = VideoCache(default_ttl=300, max_size=1000, time_func=frozen_time)
        data = self._sample_data()

        cache.set("short", data, ttl=10)
        cache.set("long", data, ttl=600)

        frozen_time.advance(11)
        assert cache.get("short") is None
        assert cache.get("long") == data

    def test_overwrite_entry(self):
        cache = VideoCache(default_ttl=60, max_size=1000)
        data_v1 = {"title": "V1"}
        data_v2 = {"title": "V2"}

        cache.set("video_1", data_v1)
        cache.set("video_1", data_v2)

        assert cache.get("video_1") == data_v2

    def test_expired_entry_is_cleaned(self, frozen_time):
        cache = VideoCache(default_ttl=60, max_size=1000, time_func=frozen_time)
        data = self._sample_data()

        cache.set("video_1", data)

        frozen_time.advance(61)
        cache.get("video_1")

        assert "video_1" not in cache._cache

    def test_evicts_oldest_when_full(self, frozen_time):
        cache = VideoCache(default_ttl=300, max_size=3, time_func=frozen_time)

        cache.set("v1", {"title": "V1"})
        frozen_time.advance(1)
        cache.set("v2", {"title": "V2"})
        frozen_time.advance(1)
        cache.set("v3", {"title": "V3"})
        frozen_time.advance(1)

        cache.set("v4", {"title": "V4"})

        assert cache.get("v1") is None
        assert cache.get("v2") is not None
        assert cache.get("v3") is not None
        assert cache.get("v4") is not None

    def test_evicts_expired_before_oldest(self, frozen_time):
        cache = VideoCache(default_ttl=300, max_size=3, time_func=frozen_time)

        cache.set("v1", {"title": "V1"})
        frozen_time.advance(1)
        cache.set("v2", {"title": "V2"}, ttl=10)
        frozen_time.advance(1)
        cache.set("v3", {"title": "V3"})

        frozen_time.advance(10)

        cache.set("v4", {"title": "V4"})

        assert cache.get("v1") is not None
        assert cache.get("v2") is None
        assert cache.get("v3") is not None
        assert cache.get("v4") is not None

    def test_overwrite_does_not_evict(self, frozen_time):
        cache = VideoCache(default_ttl=300, max_size=2, time_func=frozen_time)

        cache.set("v1", {"title": "V1"})
        cache.set("v2", {"title": "V2"})

        cache.set("v1", {"title": "V1 updated"})

        assert cache.get("v1") == {"title": "V1 updated"}
        assert cache.get("v2") is not None

    def test_cache_size_stays_within_max(self, frozen_time):
        cache = VideoCache(default_ttl=300, max_size=3, time_func=frozen_time)

        for i in range(10):
            cache.set(f"v{i}", {"title": f"V{i}"})
            frozen_time.advance(1)
            assert len(cache._cache) <= 3
