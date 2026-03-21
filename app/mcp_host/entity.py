from enum import Enum
from typing import Callable, Any, Awaitable
# ─────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────
 

class SessionStatus(str, Enum):
    """Session lifecycle states."""
    CREATED = "created"       # Allocated, no messages yet
    ACTIVE = "active"         # At least one message exchanged
    IDLE = "idle"             # No activity for idle_timeout
    EXPIRED = "expired"       # TTL exceeded, pending teardown
    TERMINATED = "terminated" # Explicitly closed or errored
 
 
class MessageRole(str, Enum):
    """Roles in the conversation history."""
    USER = "user"
    ASSISTANT = "assistant"
    TOOL_RESULT = "tool_result"
    SYSTEM = "system"
 
 
class ToolCallStatus(str, Enum):
    """Status of an MCP tool invocation."""
    PENDING = "pending"
    IN_FLIGHT = "in_flight"
    SUCCESS = "success"
    FAILED = "failed"
    TIMED_OUT = "timed_out"


# ─────────────────────────────────────────────
# Event System
# ─────────────────────────────────────────────
 
class SessionEvent(str, Enum):
    CREATED = "session.created"
    ACTIVE = "session.active"
    IDLE = "session.idle"
    EXPIRED = "session.expired"
    TERMINATED = "session.terminated"
    MESSAGE_ADDED = "session.message_added"
    TOOL_CALLED = "session.tool_called"
    CLIENT_CONNECTED = "session.client_connected"
    CLIENT_DISCONNECTED = "session.client_disconnected"
    ERROR = "session.error"
 
 
EventHandler = Callable[[SessionEvent, str, dict[str, Any]], Awaitable[None]]
