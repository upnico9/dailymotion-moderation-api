from enum import Enum


class ModerationStatus(Enum):
    PENDING = "pending"
    SPAM = "spam"
    NOT_SPAM = "not spam"

    @staticmethod
    def from_string(value: str) -> "ModerationStatus":
        for status in ModerationStatus:
            if status.value == value:
                return status
        raise ValueError(
            f"Invalid status '{value}'. Must be one of: {', '.join(s.value for s in ModerationStatus)}"
        )
