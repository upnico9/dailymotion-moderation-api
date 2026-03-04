from dataclasses import dataclass
from datetime import datetime

from domain.value_objects import ModerationStatus


@dataclass(frozen=True)
class VideoAdded:
    video_id: str
    occurred_at: datetime


@dataclass(frozen=True)
class VideoAssigned:
    video_id: str
    moderator: str
    occurred_at: datetime


@dataclass(frozen=True)
class VideoFlagged:
    video_id: str
    status: ModerationStatus
    moderator: str
    occurred_at: datetime
