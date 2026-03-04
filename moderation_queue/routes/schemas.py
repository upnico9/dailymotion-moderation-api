from pydantic import BaseModel, Field, field_validator

class AddVideoRequest(BaseModel):
    video_id: str = Field(..., description="The Dailymotion video ID", examples=["123456"])

    @field_validator("video_id", mode="before")
    @classmethod
    def coerce_video_id(cls, v):
        return str(v)


class FlagVideoRequest(BaseModel):
    video_id: str = Field(..., description="The video ID to flag", examples=["123456"])
    status: str = Field(..., description='"spam" or "not spam"', examples=["not spam"])

    @field_validator("video_id", mode="before")
    @classmethod
    def coerce_video_id(cls, v):
        return str(v)

class VideoResponse(BaseModel):
    video_id: str = Field(..., description="The video ID", examples=["123456"])


class FlagVideoResponse(BaseModel):
    video_id: str = Field(..., description="The flagged video ID", examples=["123456"])
    status: str = Field(..., description="The moderation status", examples=["not spam"])


class StatsResponse(BaseModel):
    total_pending_videos: int = Field(..., description="Videos waiting for moderation", examples=[42])
    total_spam_videos: int = Field(..., description="Videos flagged as spam", examples=[10])
    total_not_spam_videos: int = Field(..., description="Videos flagged as not spam", examples=[85])


class VideoLogEntry(BaseModel):
    date: str = Field(..., description="Timestamp of the action", examples=["2000-01-01 12:00:00"])
    status: str = Field(..., description="Video status at that point", examples=["pending"])
    moderator: str | None = Field(None, description="Moderator who performed the action", examples=["john.doe"])
