from datetime import datetime

from domain.value_objects import ModerationStatus


class Video:
    def __init__(
        self,
        video_id: str,
        status: ModerationStatus,
        assigned_moderator: str | None,
        created_at: datetime,
        updated_at: datetime,
    ):
        self.video_id = video_id
        self.status = status
        self.assigned_moderator = assigned_moderator
        self.created_at = created_at
        self.updated_at = updated_at

    def assign_to(self, moderator: str) -> None:
        self.assigned_moderator = moderator

    def flag(self, new_status: ModerationStatus) -> None:
        if self.status != ModerationStatus.PENDING:
            raise ValueError(
                f"Cannot flag video {self.video_id}: status is '{self.status.value}', expected 'pending'"
            )
        self.status = new_status

    def is_pending(self) -> bool:
        return self.status == ModerationStatus.PENDING

    def __repr__(self) -> str:
        return (
            f"Video(video_id={self.video_id!r}, status={self.status.value!r}, "
            f"assigned_moderator={self.assigned_moderator!r})"
        )


class VideoLog:
    def __init__(
        self,
        id: int,
        video_id: str,
        status: str,
        moderator: str | None,
        created_at: datetime,
    ):
        self.id = id
        self.video_id = video_id
        self.status = status
        self.moderator = moderator
        self.created_at = created_at

    def __repr__(self) -> str:
        return (
            f"VideoLog(id={self.id}, video_id={self.video_id!r}, "
            f"status={self.status!r}, moderator={self.moderator!r})"
        )
