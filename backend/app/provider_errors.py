"""Shared non-sensitive operational error contract."""


class AgentFailure(Exception):
    """Only a fixed application error code may be persisted or returned."""
