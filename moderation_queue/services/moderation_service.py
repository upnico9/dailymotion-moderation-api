from datetime import datetime, timezone

from psycopg2.errors import UniqueViolation

from domain.entities import Video
from domain.events import VideoAdded, VideoAssigned, VideoFlagged
from domain.exceptions import (
    ForbiddenError,
    InvalidStatusError,
    VideoAlreadyExistsError,
    VideoNotFoundError,
    VideoNotPendingError,
)
from domain.value_objects import ModerationStatus
from infrastructure.event_dispatcher import EventDispatcher
from repositories.video_repository import VideoRepository
from services.video_log_service import VideoLogService


class ModerationService:
    def __init__(
        self,
        video_repo: VideoRepository,
        video_log_service: VideoLogService,
        event_dispatcher: EventDispatcher,
    ):
        self._video_repo = video_repo
        self._video_log_service = video_log_service
        self._event_dispatcher = event_dispatcher
        self._register_event_listeners()

    def _register_event_listeners(self) -> None:
        self._event_dispatcher.listen(
            VideoAdded,
            lambda e: self._video_log_service.log_added(e.video_id),
        )
        self._event_dispatcher.listen(
            VideoAssigned,
            lambda e: self._video_log_service.log_assigned(e.video_id, e.moderator),
        )
        self._event_dispatcher.listen(
            VideoFlagged,
            lambda e: self._video_log_service.log_flagged(e.video_id, e.status.value, e.moderator),
        )

    def add_video(self, video_id: str) -> Video:
        try:
            video = self._video_repo.add(video_id)
        except UniqueViolation:
            raise VideoAlreadyExistsError(
                f"Video {video_id} is already in the queue"
            )

        self._event_dispatcher.dispatch(
            VideoAdded(video_id=video_id, occurred_at=datetime.now(timezone.utc))
        )
        return video

    def get_video(self, moderator: str) -> Video | None:
        video = self._video_repo.get_assigned(moderator)
        if video:
            return video

        video = self._video_repo.get_next_pending()
        if not video:
            return None

        self._video_repo.assign(video.video_id, moderator)
        self._event_dispatcher.dispatch(
            VideoAssigned(
                video_id=video.video_id,
                moderator=moderator,
                occurred_at=datetime.now(timezone.utc),
            )
        )
        return self._video_repo.get_by_id(video.video_id)

    def flag_video(self, video_id: str, status: str, moderator: str) -> Video:
        video = self._video_repo.get_by_id(video_id)
        if not video:
            raise VideoNotFoundError(f"Video {video_id} not found")

        if video.assigned_moderator != moderator:
            raise ForbiddenError(
                f"Video {video_id} is not assigned to {moderator}"
            )

        try:
            moderation_status = ModerationStatus.from_string(status)
        except ValueError:
            raise InvalidStatusError(
                f"Invalid status '{status}'. Must be 'spam' or 'not spam'"
            )

        try:
            video.flag(moderation_status)
        except ValueError:
            raise VideoNotPendingError(
                f"Video {video_id} is not pending, cannot flag"
            )

        self._video_repo.flag(video_id, status)
        self._event_dispatcher.dispatch(
            VideoFlagged(
                video_id=video_id,
                status=moderation_status,
                moderator=moderator,
                occurred_at=datetime.now(timezone.utc),
            )
        )
        return self._video_repo.get_by_id(video_id)

    def get_stats(self) -> dict:
        return self._video_repo.count_by_status()
