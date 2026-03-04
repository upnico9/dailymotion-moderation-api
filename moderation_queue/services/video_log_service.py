from domain.entities import VideoLog
from repositories.video_log_repository import VideoLogRepository


class VideoLogService:
    def __init__(self, video_log_repo: VideoLogRepository):
        self._video_log_repo = video_log_repo

    def log_added(self, video_id: str) -> VideoLog:
        return self._video_log_repo.create(video_id, "pending", None)

    def log_assigned(self, video_id: str, moderator: str) -> VideoLog:
        return self._video_log_repo.create(video_id, "pending", moderator)

    def log_flagged(self, video_id: str, status: str, moderator: str) -> VideoLog:
        return self._video_log_repo.create(video_id, status, moderator)

    def get_video_logs(self, video_id: str) -> list[dict]:
        logs = self._video_log_repo.get_by_video_id(video_id)
        return [
            {
                "date": log.created_at.isoformat(),
                "status": log.status,
                "moderator": log.moderator,
            }
            for log in logs
        ]
