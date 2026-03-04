from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response

from middleware.auth import get_current_moderator
from routes.schemas import (
    AddVideoRequest,
    FlagVideoRequest,
    VideoResponse,
    FlagVideoResponse,
    StatsResponse,
    VideoLogEntry,
)
from services.moderation_service import ModerationService
from services.video_log_service import VideoLogService

router = APIRouter(tags=["Moderation"])

def get_moderation_service(request: Request) -> ModerationService:
    return request.app.state.moderation_service


def get_video_log_service(request: Request) -> VideoLogService:
    return request.app.state.video_log_service


@router.post(
    "/add_video",
    status_code=201,
    response_model=VideoResponse,
    summary="Add a video to the moderation queue",
    description="Called server-to-server when a new video is uploaded on Dailymotion.",
)
def add_video(
    body: AddVideoRequest,
    service: ModerationService = Depends(get_moderation_service),
):
    video = service.add_video(body.video_id)
    return {"video_id": video.video_id}


@router.get(
    "/get_video",
    response_model=VideoResponse,
    summary="Get the next video to moderate",
    description="Returns the next pending video for the authenticated moderator (FIFO). "
    "Same moderator gets the same video. Different moderators get different videos.",
)
def get_video(
    moderator: str = Depends(get_current_moderator),
    service: ModerationService = Depends(get_moderation_service),
):
    video = service.get_video(moderator)
    if not video:
        return Response(status_code=204)
    return {"video_id": video.video_id}


@router.post(
    "/flag_video",
    response_model=FlagVideoResponse,
    summary="Flag a video as spam or not spam",
    description='The authenticated moderator flags their assigned video. Status must be "spam" or "not spam".',
)
def flag_video(
    body: FlagVideoRequest,
    moderator: str = Depends(get_current_moderator),
    service: ModerationService = Depends(get_moderation_service),
):
    video = service.flag_video(body.video_id, body.status, moderator)
    return {"video_id": video.video_id, "status": video.status.value}


@router.get(
    "/stats",
    response_model=StatsResponse,
    summary="Get moderation queue statistics",
    description="Returns the count of pending, spam, and not spam videos.",
)
def stats(
    service: ModerationService = Depends(get_moderation_service),
):
    return service.get_stats()


@router.get(
    "/log_video/{video_id}",
    response_model=list[VideoLogEntry],
    summary="Get moderation history for a video",
    description="Returns the chronological moderation history for a given video.",
)
def log_video(
    video_id: str,
    video_log_service: VideoLogService = Depends(get_video_log_service),
):
    return video_log_service.get_video_logs(video_id)
