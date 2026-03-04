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
        cache = VideoCache()
        data = self._sample_data()

        cache.set("video_1", data)
        result = cache.get("video_1")

        assert result == data

    def test_get_expired(self):
        cache = VideoCache()
        data = self._sample_data()

        cache.set("video_1", data, ttl=0)
        time.sleep(0.01)
        result = cache.get("video_1")

        assert result is None

    def test_get_expired_with_frozen_time(self, frozen_time):
        cache = VideoCache(default_ttl=60, time_func=frozen_time)
        data = self._sample_data()

        cache.set("video_1", data)

        frozen_time.advance(59)
        assert cache.get("video_1") == data

        frozen_time.advance(2)
        assert cache.get("video_1") is None

    def test_get_missing(self):
        cache = VideoCache()

        result = cache.get("nonexistent")

        assert result is None

    def test_invalidate(self):
        cache = VideoCache()
        data = self._sample_data()

        cache.set("video_1", data)
        cache.invalidate("video_1")
        result = cache.get("video_1")

        assert result is None

    def test_invalidate_nonexistent(self):
        cache = VideoCache()

        cache.invalidate("nonexistent")

    def test_clear(self):
        cache = VideoCache()
        data = self._sample_data()

        cache.set("video_1", data)
        cache.set("video_2", data)
        cache.set("video_3", data)

        cache.clear()

        assert cache.get("video_1") is None
        assert cache.get("video_2") is None
        assert cache.get("video_3") is None

    def test_custom_ttl_per_entry(self, frozen_time):
        cache = VideoCache(default_ttl=300, time_func=frozen_time)
        data = self._sample_data()

        cache.set("short", data, ttl=10)
        cache.set("long", data, ttl=600)

        frozen_time.advance(11)
        assert cache.get("short") is None
        assert cache.get("long") == data

    def test_overwrite_entry(self):
        cache = VideoCache(default_ttl=60)
        data_v1 = {"title": "V1"}
        data_v2 = {"title": "V2"}

        cache.set("video_1", data_v1)
        cache.set("video_1", data_v2)

        assert cache.get("video_1") == data_v2

    def test_expired_entry_is_cleaned(self, frozen_time):
        cache = VideoCache(default_ttl=60, time_func=frozen_time)
        data = self._sample_data()

        cache.set("video_1", data)

        frozen_time.advance(61)
        cache.get("video_1")

        assert "video_1" not in cache._cache
