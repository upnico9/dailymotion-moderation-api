import pytest


class FrozenTime:

    def __init__(self, initial: float = 1000.0):
        self.current = initial

    def __call__(self) -> float:
        return self.current

    def advance(self, seconds: float) -> None:
        self.current += seconds


@pytest.fixture
def frozen_time():
    return FrozenTime()
