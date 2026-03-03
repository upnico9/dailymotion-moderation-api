from psycopg2 import pool

from domain.entities import Video
from domain.value_objects import ModerationStatus
from infrastructure.database import get_connection


class VideoRepository:
    def __init__(self, connection_pool: pool.ThreadedConnectionPool):
        self._pool = connection_pool

    def add(self, video_id: str) -> Video:
        with get_connection(self._pool) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO videos_queue (video_id) VALUES (%s) RETURNING *",
                    (video_id,),
                )
                return self._row_to_entity(cur.fetchone())

    def get_by_id(self, video_id: str) -> Video | None:
        with get_connection(self._pool) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM videos_queue WHERE video_id = %s",
                    (video_id,),
                )
                row = cur.fetchone()
                return self._row_to_entity(row) if row else None

    def get_assigned(self, moderator: str) -> Video | None:
        with get_connection(self._pool) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM videos_queue WHERE status = 'pending' AND assigned_moderator = %s",
                    (moderator,),
                )
                row = cur.fetchone()
                return self._row_to_entity(row) if row else None

    def get_next_pending(self) -> Video | None:
        with get_connection(self._pool) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT * FROM videos_queue
                    WHERE status = 'pending' AND assigned_moderator IS NULL
                    ORDER BY created_at ASC
                    LIMIT 1
                    FOR UPDATE SKIP LOCKED
                    """
                )
                row = cur.fetchone()
                return self._row_to_entity(row) if row else None

    def assign(self, video_id: str, moderator: str) -> None:
        with get_connection(self._pool) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE videos_queue SET assigned_moderator = %s, updated_at = NOW() WHERE video_id = %s",
                    (moderator, video_id),
                )

    def flag(self, video_id: str, status: str) -> None:
        with get_connection(self._pool) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE videos_queue SET status = %s, updated_at = NOW() WHERE video_id = %s",
                    (status, video_id),
                )

    def count_by_status(self) -> dict:
        with get_connection(self._pool) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        COUNT(*) FILTER (WHERE status = 'pending') AS pending,
                        COUNT(*) FILTER (WHERE status = 'spam') AS spam,
                        COUNT(*) FILTER (WHERE status = 'not spam') AS not_spam
                    FROM videos_queue
                    """
                )
                row = cur.fetchone()
                return {
                    "total_pending_videos": row[0],
                    "total_spam_videos": row[1],
                    "total_not_spam_videos": row[2],
                }

    @staticmethod
    def _row_to_entity(row) -> Video:
        return Video(
            video_id=row[0],
            status=ModerationStatus.from_string(row[1]),
            assigned_moderator=row[2],
            created_at=row[3],
            updated_at=row[4],
        )
