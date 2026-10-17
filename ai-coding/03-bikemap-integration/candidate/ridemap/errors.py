"""Errors raised by ridemap."""


class RidemapError(Exception):
    """Base class for ridemap errors."""


class TrackError(RidemapError):
    """The ride file is missing or malformed."""


class MapDrawError(RidemapError):
    """MapDraw answered with an error."""

    def __init__(self, status, message):
        super().__init__(f"MapDraw {status}: {message}")
        self.status = status
        self.message = message
