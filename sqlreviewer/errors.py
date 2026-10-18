"""Exceptions whose messages are always safe to show to the user."""


class ReviewError(Exception):
    """Base class. str(error) is a user-safe message (no secrets, no raw API text)."""

    def __init__(self, user_message: str):
        super().__init__(user_message)
        self.user_message = user_message


class ValidationError(ReviewError):
    """The submitted input is not acceptable."""


class ConfigError(ReviewError):
    """Required configuration (such as the API key) is missing."""


class APIError(ReviewError):
    """The AI service call failed (rate limit, network, auth, ...)."""


class ResponseFormatError(ReviewError):
    """The AI service answered, but not in the expected format."""
