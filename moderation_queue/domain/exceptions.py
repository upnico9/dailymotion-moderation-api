class VideoNotFoundError(Exception):
    """Not existing video"""
    pass


class VideoAlreadyExistsError(Exception):
    """Video already in the queue"""
    pass


class VideoNotPendingError(Exception):
    """Can't flag a video that is not pending"""
    pass


class InvalidStatusError(Exception):
    """Bad status for a video update"""
    pass


class AuthorizationError(Exception):
    """Invalid or no authorization header"""
    pass


class ForbiddenError(Exception):
    """Authenticated but not allowed to perform this action"""
    pass


class InvalidRequestError(Exception):
    """Bad request"""
    pass
