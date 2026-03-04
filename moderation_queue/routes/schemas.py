from pydantic import BaseModel, field_validator


class AddVideoRequest(BaseModel):
    video_id: str

    @field_validator("video_id", mode="before")
    @classmethod
    def coerce_video_id(cls, v):
        return str(v)


class FlagVideoRequest(BaseModel):
    video_id: str
    status: str

    @field_validator("video_id", mode="before")
    @classmethod
    def coerce_video_id(cls, v):
        return str(v)
