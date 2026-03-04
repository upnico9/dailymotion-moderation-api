class VideoNotFoundError(Exception):
    """Vidéo introuvable sur l'API Dailymotion."""
    pass


class DailymotionApiError(Exception):
    """Erreur générique lors de l'appel à l'API Dailymotion."""
    pass
