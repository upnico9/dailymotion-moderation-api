from psycopg2 import pool

from domain.entities import VideoLog
from infrastructure.database import get_connection


class VideoLogRepository:
    def __init__(self, connection_pool: pool.ThreadedConnectionPool):
        self._pool = connection_pool

    def create(self, video_id: str, status: str, moderator: str | None = None) -> VideoLog:
        with get_connection(self._pool) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO video_logs (video_id, status, moderator) VALUES (%s, %s, %s) RETURNING *",
                    (video_id, status, moderator),
                )
                return self._row_to_entity(cur.fetchone())

    def get_by_video_id(self, video_id: str) -> list[VideoLog]:
        with get_connection(self._pool) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM video_logs WHERE video_id = %s ORDER BY created_at ASC",
                    (video_id,),
                )
                return [self._row_to_entity(row) for row in cur.fetchall()]

    @staticmethod
    def _row_to_entity(row) -> VideoLog:
        return VideoLog(
            id=row[0],
            video_id=row[1],
            status=row[2],
            moderator=row[3],
            created_at=row[4],
        )
