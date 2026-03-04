from typing import Callable


class EventDispatcher:
    def __init__(self):
        self._listeners: dict[type, list[Callable]] = {}

    def listen(self, event_type: type, callback: Callable) -> None:
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(callback)

    def dispatch(self, event) -> None:
        event_type = type(event)
        for callback in self._listeners.get(event_type, []):
            callback(event)
