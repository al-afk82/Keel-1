"""Mention handling shared across agents.

The coordinator addresses an agent inside the shared session by prefixing the
message content with a Band mention token, @[[uuid]], followed by a space and
the real payload. Agents that parse the payload as JSON must remove this token
first or the parse fails.
"""

import re

_MENTION_PREFIX = re.compile(r"^\s*(@\[\[[0-9a-fA-F-]+\]\]\s*)+")


def strip_mentions(content: str) -> str:
    """Remove one or more leading @[[uuid]] mention tokens from content."""
    if not isinstance(content, str):
        return content
    return _MENTION_PREFIX.sub("", content).strip()


def clean_messages(messages: list) -> list:
    """Return messages with leading mention tokens stripped from string content.

    Generic across agents. Leaves non-string content and message structure
    untouched, so it is safe for any LangChain message list.
    """
    cleaned = []
    for m in messages:
        content = getattr(m, "content", None)
        if isinstance(content, str):
            stripped = strip_mentions(content)
            if stripped != content:
                try:
                    m = m.model_copy(update={"content": stripped})
                except Exception:
                    m.content = stripped
        cleaned.append(m)
    return cleaned
