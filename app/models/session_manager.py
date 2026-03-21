from datetime import time
import uuid

from typing import Any

from dataclasses import dataclass, field


from app.mcp_host.entity import MessageRole, ToolCallStatus, SessionStatus
from app.exception import SessionLimitError
 
@dataclass
class Message:
    """A single message in the conversation history."""
    role: MessageRole
    content: str
    timestamp: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)
    token_count: int | None = None  # For context window tracking
 
 
@dataclass
class ToolCall:
    """Record of an MCP tool invocation."""
    call_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    server_name: str = ""          # Which MCP server owns this tool
    tool_name: str = ""            # Tool identifier
    arguments: dict[str, Any] = field(default_factory=dict)
    result: Any = None
    error: str | None = None
    status: ToolCallStatus = ToolCallStatus.PENDING
    created_at: float = field(default_factory=time.time)
    completed_at: float | None = None
    duration_ms: float | None = None
 
 
@dataclass
class ClientConnection:
    """Reference to an active MCP client connection."""
    server_name: str
    transport_type: str            # "stdio" | "sse" | "streamable_http"
    server_url: str | None = None  # For remote servers
    client_instance: Any = None    # The actual MCP Client SDK object
    connected_at: float = field(default_factory=time.time)
    capabilities: dict[str, Any] = field(default_factory=dict)  # From initialize handshake
    available_tools: list[dict[str, Any]] = field(default_factory=list)
    is_healthy: bool = True
 
 
@dataclass
class UserContext:
    """User-specific context scoped to this session."""
    user_id: str = ""
    preferences: dict[str, Any] = field(default_factory=dict)  # language, timezone, format
    auth_tokens: dict[str, str] = field(default_factory=dict)  # server_name -> oauth token
    permissions: set[str] = field(default_factory=set)          # Allowed tool scopes
    custom_data: dict[str, Any] = field(default_factory=dict)   # App-specific
 
 
@dataclass
class ConversationHistory:
    """
    Manages the message list with context window awareness.
    Handles truncation strategies when history exceeds token limits.
    """
    messages: list[Message] = field(default_factory=list)
    max_tokens: int = 100_000       # LLM context window budget for history
    summary: str | None = None      # Compressed summary of older messages
    total_tokens_used: int = 0
 
    def add_message(self, message: Message) -> None:
        self.messages.append(message)
        if message.token_count:
            self.total_tokens_used += message.token_count
        self._enforce_limits()
 
    def get_context_messages(self) -> list[dict[str, str]]:
        """
        Returns messages formatted for the LLM API call.
        Prepends the rolling summary if older messages were compressed.
        """
        result = []
        if self.summary:
            result.append({
                "role": "system",
                "content": f"Summary of earlier conversation:\n{self.summary}",
            })
        for msg in self.messages:
            result.append({"role": msg.role.value, "content": msg.content})
        return result
 
    def _enforce_limits(self) -> None:
        """
        Truncation strategy: sliding window with summary.
        When total tokens exceed budget, compress oldest messages
        into the rolling summary and remove them.
        """
        if self.total_tokens_used <= self.max_tokens:
            return
 
        overflow = self.total_tokens_used - self.max_tokens
        removed_content: list[str] = []
        removed_tokens = 0
 
        while self.messages and removed_tokens < overflow:
            oldest = self.messages.pop(0)
            removed_content.append(f"[{oldest.role.value}]: {oldest.content}")
            removed_tokens += oldest.token_count or 0
 
        self.total_tokens_used -= removed_tokens
 
        # In production, you'd call the LLM to summarize removed_content.
        # Here we store the raw text as a placeholder.
        compressed = "\n".join(removed_content)
        if self.summary:
            self.summary += f"\n{compressed}"
        else:
            self.summary = compressed
 
 
@dataclass
class ToolContext:
    """Tracks all tool calls in the session."""
    calls: list[ToolCall] = field(default_factory=list)
    call_count: int = 0
    max_calls_per_session: int = 200  # Rate limit
 
    def record_call(self, tool_call: ToolCall) -> ToolCall:
        if self.call_count >= self.max_calls_per_session:
            raise SessionLimitError(
                f"Tool call limit ({self.max_calls_per_session}) exceeded"
            )
        self.calls.append(tool_call)
        self.call_count += 1
        return tool_call
 
    def get_pending(self) -> list[ToolCall]:
        return [c for c in self.calls if c.status in (
            ToolCallStatus.PENDING, ToolCallStatus.IN_FLIGHT
        )]
 
    def get_last_result(self, tool_name: str) -> Any | None:
        """Retrieve the most recent successful result for a given tool."""
        for call in reversed(self.calls):
            if call.tool_name == tool_name and call.status == ToolCallStatus.SUCCESS:
                return call.result
        return None
 
 
# ─────────────────────────────────────────────
# Session Object (top-level aggregate)
# ─────────────────────────────────────────────
 
@dataclass
class Session:
    """
    The complete session state object.
    One instance per active conversation in the MCP host.
    """
    # Identity
    session_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    status: SessionStatus = SessionStatus.CREATED
 
    # Timestamps
    created_at: float = field(default_factory=time.time)
    last_activity_at: float = field(default_factory=time.time)
    expires_at: float | None = None  # Set by TTL policy
 
    # Core components
    user: UserContext = field(default_factory=UserContext)
    conversation: ConversationHistory = field(default_factory=ConversationHistory)
    tools: ToolContext = field(default_factory=ToolContext)
    connections: dict[str, ClientConnection] = field(default_factory=dict)
 
    # Configuration
    idle_timeout_sec: float = 300.0   # 5 min → idle
    max_ttl_sec: float = 3600.0       # 1 hour hard limit
    system_prompt: str = ""           # LLM persona for this session
 
    def touch(self) -> None:
        """Update last activity and reactivate if idle."""
        self.last_activity_at = time.time()
        if self.status == SessionStatus.IDLE:
            self.status = SessionStatus.ACTIVE
 
    def is_expired(self) -> bool:
        now = time.time()
        hard_expired = (now - self.created_at) > self.max_ttl_sec
        idle_expired = (now - self.last_activity_at) > self.idle_timeout_sec
        return hard_expired or idle_expired
 
    def get_connection(self, server_name: str) -> ClientConnection | None:
        """Lazy lookup — returns None if not yet connected."""
        return self.connections.get(server_name)
 
    def register_connection(self, conn: ClientConnection) -> None:
        self.connections[conn.server_name] = conn
 
    def get_aggregated_tools(self) -> list[dict[str, Any]]:
        """
        Collect all available tools from all connected MCP servers.
        This is what gets passed to the LLM as the tool catalog.
        """
        tools = []
        for conn in self.connections.values():
            if conn.is_healthy:
                for tool in conn.available_tools:
                    tools.append({
                        **tool,
                        "_server": conn.server_name,  # Internal routing tag
                    })
        return tools
 