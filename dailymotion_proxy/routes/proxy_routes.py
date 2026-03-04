from fastapi import APIRouter, Request

from services.proxy_service import ProxyService

router = APIRouter()


def get_proxy_service(request: Request) -> ProxyService:
    return request.app.state.proxy_service


@router.get("/get_video_info/{video_id}")
def get_video_info(video_id: str, request: Request):
    service = get_proxy_service(request)
    return service.get_video_info(video_id)
