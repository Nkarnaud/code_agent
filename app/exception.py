# ─────────────────────────────────────────────
# Exceptions
# ─────────────────────────────────────────────
 
class SessionError(Exception):
    """Base exception for session operations."""
    pass
 
class SessionNotFoundError(SessionError):
    pass
 
class SessionExpiredError(SessionError):
    pass
 
class SessionLimitError(SessionError):
    pass
