from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response

from middleware.auth import get_current_moderator
from routes.schemas import AddVideoRequest, FlagVideoRequest
from services.moderation_service import ModerationService
from services.video_log_service import VideoLogService

router = APIRouter()

def get_moderation_service(request: Request) -> ModerationService:
    return request.app.state.moderation_service


def get_video_log_service(request: Request) -> VideoLogService:
    return request.app.state.video_log_service


@router.post("/add_video", status_code=201)
def add_video(
    body: AddVideoRequest,
    service: ModerationService = Depends(get_moderation_service),
):
    video = service.add_video(body.video_id)
    return {"video_id": video.video_id}


@router.get("/get_video")
def get_video(
    moderator: str = Depends(get_current_moderator),
    service: ModerationService = Depends(get_moderation_service),
):
    video = service.get_video(moderator)
    if not video:
        return Response(status_code=204)
    return {"video_id": video.video_id}


@router.post("/flag_video")
def flag_video(
    body: FlagVideoRequest,
    moderator: str = Depends(get_current_moderator),
    service: ModerationService = Depends(get_moderation_service),
):
    video = service.flag_video(body.video_id, body.status, moderator)
    return {"video_id": video.video_id, "status": video.status.value}


@router.get("/stats")
def stats(
    service: ModerationService = Depends(get_moderation_service),
):
    return service.get_stats()


@router.get("/log_video/{video_id}")
def log_video(
    video_id: str,
    video_log_service: VideoLogService = Depends(get_video_log_service),
):
    return video_log_service.get_video_logs(video_id)
