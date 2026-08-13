"""Groq agent loop for the WMS chatbot.

Uses Groq's OpenAI-compatible chat completions API with function calling. The
agent loop: send the conversation + tool schemas to the model, run any tool it
asks for, feed the result back as ``role: tool`` messages, and repeat until the
model writes a plain-text answer.

History is a list of OpenAI-style message dicts:
    {"role": "user"|"assistant"|"tool", "content": ..., "tool_calls": ...}
"""
import json
from typing import Any, Dict, List

from core import logger
from core.config import settings
from core.services.chatbot.tools import TOOLS, run_tool

logging = logger(__name__)

MAX_TOOL_TURNS = 5

SYSTEM_INSTRUCTION = """
You are the Whitfield WMS Assistant, a helpful warehouse management assistant for
Dan Whitfield's fulfilment operation (warehouses in Reno, NV and Columbus, OH).

# Your job
Answer staff and manager questions using live data from the warehouse management
system. You have read-only tools to query stock, products, orders, shipments, bin
locations, low-stock items, sellers, and warehouse procedures. Use them whenever
the answer depends on current data. Never invent a stock level, order status, or
location — always call a tool to look it up.

# Response rules
- Be concise and practical. Use short sentences.
- When reporting stock, give the warehouse name and the available/good/reserved
  numbers clearly.
- If a tool returns an error (e.g. product not found), say so plainly and ask the
  user to confirm the reference/name.
- Do not use markdown headings or bullet lists unless they genuinely help (e.g. a
  short list of low-stock items).

# Safety
You may only read data. You must refuse (politely) any request to modify, delete,
or bypass warehouse data — point the user to a manager or the system admin.
"""


def _groq_client():
    """Lazily build the Groq async client from settings.

    Returns:
        The async Groq client.

    Raises:
        RuntimeError: If GROQ_API_KEY is not configured.
    """
    key = settings.groq_api_key
    if not key:
        raise RuntimeError(
            "GROQ_API_KEY is missing from .env. Chatbot tools work, but the LLM cannot answer."
        )
    from groq import AsyncGroq

    return AsyncGroq(api_key=key)


def _groq_tools() -> List[Dict[str, Any]]:
    """Convert the WMS tool schemas to Groq's OpenAI-compatible tool format.

    Groq wraps each tool as ``{"type": "function", "function": {name, description,
    parameters}}``.

    Returns:
        list: Groq tool definitions.
    """
    tools = []
    for schema in TOOLS:
        tools.append(
            {
                "type": "function",
                "function": {
                    "name": schema["name"],
                    "description": schema["description"],
                    "parameters": schema["parameters"],
                },
            }
        )
    return tools


class AgentLoop:
    """Encapsulates the Groq tool-calling agent loop."""

    def __init__(self) -> None:
        """Initialize the model name."""
        self.model = settings.groq_model
        self._client = None

    @property
    def client(self):
        """Return (and cache) the Groq async client.

        Returns:
            The async Groq client.
        """
        if self._client is None:
            self._client = _groq_client()
        return self._client

    async def run(self, history: list, max_turns: int = MAX_TOOL_TURNS):
        """Run the agent loop over a conversation and return the final answer.

        Args:
            history: Conversation history (OpenAI-style message dicts), mutated.
            max_turns: Safety limit on tool-calling rounds.

        Returns:
            tuple: (answer_text, tool_calls_made) where tool_calls_made is a list
                of (name, arguments).
        """
        calls: List[tuple] = []
        for _ in range(max_turns):
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": SYSTEM_INSTRUCTION}] + history,
                tools=_groq_tools(),
                tool_choice="auto",
            )
            message = response.choices[0].message
            if message.tool_calls:
                await self._handle_tool_calls(message, history, calls)
                continue
            # Plain answer — done.
            history.append({"role": "assistant", "content": message.content})
            return message.content, calls
        # Safety: exhausted turns; return last assistant text if any.
        last = next((m for m in reversed(history) if m.get("role") == "assistant"), {})
        return last.get("content", ""), calls

    async def _handle_tool_calls(self, message, history, calls) -> None:
        """Run the tool calls in an assistant message and append results.

        Args:
            message: The assistant chat completion message (with tool_calls).
            history: The conversation history (mutated).
            calls: Accumulator of (name, arguments).
        """
        assistant_msg = {
            "role": "assistant",
            "content": message.content,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in message.tool_calls
            ],
        }
        history.append(assistant_msg)
        for tc in message.tool_calls:
            arguments = json.loads(tc.function.arguments or "{}")
            result = await run_tool(tc.function.name, arguments)
            history.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "name": tc.function.name,
                    "content": json.dumps(result, default=str),
                }
            )
            calls.append((tc.function.name, arguments))
