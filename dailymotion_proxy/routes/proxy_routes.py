from pydantic import BaseModel, Field
from fastapi import APIRouter, Request

from services.proxy_service import ProxyService

router = APIRouter(tags=["Proxy"])


class VideoInfoResponse(BaseModel):
    title: str = Field(..., description="Video title", examples=["Dailymotion Spirit Movie"])
    channel: str = Field(..., description="Video channel", examples=["creation"])
    owner: str = Field(..., description="Video owner username", examples=["dailymotion"])


def get_proxy_service(request: Request) -> ProxyService:
    return request.app.state.proxy_service


@router.get(
    "/get_video_info/{video_id}",
    response_model=VideoInfoResponse,
    summary="Get video information from Dailymotion",
    description="Proxies the Dailymotion API to retrieve video metadata. "
    "Results are cached (5 min TTL). Video IDs ending with 404 return a 404.",
)
def get_video_info(video_id: str, request: Request):
    service = get_proxy_service(request)
    return service.get_video_info(video_id)
