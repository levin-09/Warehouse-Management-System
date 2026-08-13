"""Chat service — per-session conversation management.

Holds conversation history per ``session_id`` so different users/rooms never
share a conversation. History is a list of OpenAI-style message dicts (Groq's
format). Kept in memory for the process lifetime; swap for MongoDB persistence
if it needs to survive restarts.
"""
import json
from typing import Any, Dict, List

from core import logger
from core.services.chatbot.agent import MAX_TOOL_TURNS, SYSTEM_INSTRUCTION, AgentLoop, _groq_tools

logging = logger(__name__)


def _sse(event: str, data: Dict[str, Any]) -> str:
    """Format one Server-Sent Event string.

    Args:
        event: Event name (delta/tool_call/tool_result/error/done).
        data: Event payload.

    Returns:
        str: A formatted SSE message.
    """
    return f"event: {event}\ndata: {json.dumps(data, default=str)}\n\n"


class ChatService:
    """Manages per-session history and drives the agent loop."""

    def __init__(self) -> None:
        """Initialize the session store and agent loop."""
        self._sessions: Dict[str, list] = {}
        self._agent = AgentLoop()

    def _history(self, session_id: str) -> list:
        """Return (creating if needed) the history for a session.

        Args:
            session_id: The conversation session id.

        Returns:
            list: The session's history.
        """
        return self._sessions.setdefault(session_id, [])

    def history(self, session_id: str) -> List[Dict[str, Any]]:
        """Return a copy of the conversation history for a session.

        Args:
            session_id: The conversation session id.

        Returns:
            list: Copy of the session history.
        """
        return list(self._history(session_id))

    def reset(self, session_id: str) -> None:
        """Clear a session's history.

        Args:
            session_id: The conversation session id.
        """
        self._sessions.pop(session_id, None)

    async def chat(self, session_id: str, user_input: str) -> Dict[str, Any]:
        """Append a user turn and run the agent loop.

        Args:
            session_id: The conversation session id.
            user_input: The user's message.

        Returns:
            dict: ``{"response": str, "session_id": str, "tool_calls": [...]}``.

        Raises:
            RuntimeError: If the Groq API key is not configured.
        """
        history = self._history(session_id)
        history.append({"role": "user", "content": user_input})
        answer, calls = await self._agent.run(history)
        return {
            "response": answer,
            "session_id": session_id,
            "tool_calls": [{"name": n, "arguments": a} for n, a in calls],
        }

    async def stream(self, session_id: str, user_input: str):
        """Stream a chat reply as Server-Sent Events.

        Yields the same SSE events as before: ``delta``, ``tool_call``,
        ``tool_result``, ``error``, ``done``.

        Args:
            session_id: The conversation session id.
            user_input: The user's message.

        Yields:
            str: Formatted SSE events.
        """
        history = self._history(session_id)
        history.append({"role": "user", "content": user_input})

        async def generator():
            chunks = []
            calls: List[tuple] = []
            try:
                for _ in range(MAX_TOOL_TURNS):
                    stream = await self._agent.client.chat.completions.create(
                        model=self._agent.model,
                        messages=[{"role": "system", "content": SYSTEM_INSTRUCTION}] + history,
                        tools=_groq_tools(),
                        tool_choice="auto",
                        stream=True,
                    )
                    # Accumulate streamed tool calls by index.
                    tool_acc: Dict[int, Dict[str, str]] = {}
                    async for chunk in stream:
                        if not chunk.choices:
                            continue
                        delta = chunk.choices[0].delta
                        if getattr(delta, "content", None):
                            chunks.append(delta.content)
                            yield _sse("delta", {"text": delta.content})
                        for tc in (getattr(delta, "tool_calls", None) or []):
                            acc = tool_acc.setdefault(tc.index, {"id": "", "name": "", "arguments": ""})
                            if tc.id:
                                acc["id"] = tc.id
                            if tc.function and tc.function.name:
                                acc["name"] += tc.function.name
                            if tc.function and tc.function.arguments:
                                acc["arguments"] += tc.function.arguments
                            if acc["name"]:
                                yield _sse("tool_call", {"name": acc["name"]})

                    if not tool_acc:
                        break

                    # Append the assistant message with tool calls.
                    history.append(
                        {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": a["id"],
                                    "type": "function",
                                    "function": {"name": a["name"], "arguments": a["arguments"]},
                                }
                                for a in tool_acc.values()
                            ],
                        }
                    )
                    for a in tool_acc.values():
                        arguments = json.loads(a["arguments"] or "{}")
                        result = await _agent_run_tool(a["name"], arguments)
                        history.append(
                            {
                                "role": "tool",
                                "tool_call_id": a["id"],
                                "name": a["name"],
                                "content": json.dumps(result, default=str),
                            }
                        )
                        calls.append((a["name"], arguments))
                    yield _sse("tool_result", {"count": len(tool_acc)})
            except Exception as error:
                logging.error(f"Chat streaming error: {error}")
                yield _sse("error", {"message": str(error)})
            finally:
                text = "".join(chunks)
                if text:
                    history.append({"role": "assistant", "content": text})
            yield _sse("done", {"response": "".join(chunks)})

        from fastapi.responses import StreamingResponse

        return StreamingResponse(
            generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )


async def _agent_run_tool(name: str, arguments: dict):
    """Run a tool and return its result (used by the stream generator).

    Args:
        name: Tool name.
        arguments: Tool arguments.

    Returns:
        dict: Tool result.
    """
    from core.services.chatbot.tools import run_tool

    return await run_tool(name, arguments)
