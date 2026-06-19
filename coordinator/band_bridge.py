#!/usr/bin/env python3
"""
Band Bridge

Translates the C++ coordinator's sync HTTP calls into Band messages.
Runs on port 5000, matching the mock_server interface exactly.
The C++ coordinator needs BAND_HOST=http://127.0.0.1:5000 (unchanged).

Model: one shared session holds the coordinator and all agents. To target an
agent the bridge posts into that single room with an at mention prefix, so only
the named agent responds. Replies land in the same room and are matched back to
the caller by sender id.

Setup before first run:
  1. Register the coordinator as a Band agent — get its agent_id and api_key.
  2. Run setup_session.py to create the session and add every participant.
  3. Put COORDINATOR_AGENT_ID, COORDINATOR_API_KEY and SESSION_ROOM_ID in .env.
  4. Run: python3 band_bridge.py
"""

import asyncio
import json
import logging
import os
import re
from collections import deque

from aiohttp import web
from band.client.rest import (
    ChatMessageRequest,
    ChatMessageRequestMentionsItem,
    DEFAULT_REQUEST_OPTIONS,
)
from band.platform.event import MessageEvent, RoomAddedEvent
from band.platform.link import BandLink
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [BRIDGE] %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

COORDINATOR_AGENT_ID: str = os.getenv("COORDINATOR_AGENT_ID", "")
COORDINATOR_API_KEY: str = os.getenv("COORDINATOR_API_KEY", "")
SESSION_ROOM_ID: str = os.getenv("SESSION_ROOM_ID", "")

# Port 5000 is held by the drift harness backend. The bridge listens here and
# the C++ coordinator's BAND_HOST must point at the same port.
BRIDGE_PORT: int = int(os.getenv("BRIDGE_PORT", "5055"))

# How long to wait for an agent's verdict before giving up. An LLM round trip
# takes several seconds, so this must comfortably exceed model latency.
REPLY_TIMEOUT: float = float(os.getenv("BRIDGE_REPLY_TIMEOUT", "30"))

# How an agent is tagged inside a message. Band renders @[[uuid]] as the agent's
# name. If the first live test shows the wrong agent responding, this is the one
# line to change.
MENTION_TEMPLATE: str = "@[[{uuid}]] "

AGENT_UUIDS: dict[str, str] = {
    "01-logger":             "b4fa1211-d6a7-4171-9351-d633d83bd06c",
    "03-human-profiler":     "5d486be4-f3fd-4e79-9da5-18cf10ca2f45",
    "04-engine-profiler":    "2a4b901a-c078-4a7f-bc80-bfe0e779c7d8",
    "05-alignment-classifier": "007d56f5-6695-47ce-be88-c245586adf59",
    "06-question-generator": "71a21a6f-3af3-4408-99f1-f811ed562462",
    "07-gap-analyzer":       "db01f764-6518-4aed-be28-14a97ec043eb",
    "08-constraints-checker":"311e1eb1-a3de-4541-b3bb-a2db48b1239f",
    "09-anti-patterns-checker": "0d062438-b3fe-47c8-bb36-9334465b2868",
    "10-voice-checker":      "2576cb68-7675-4903-ae62-ee7e22267a4f",
    "11-quality-checker":    "d338c531-e1df-4952-ab33-a71a8407a798",
    "12-identity-agent":     "ed23a4ac-ac52-444c-bd23-fb33c1a23346",
    "13-verifier":           "00545343-7a7b-493a-828d-71ec34b1bfd1",
    "14-harness-logger":     "d3e3a448-31db-45b0-8b6e-b1a65984bc58",
}

UUID_TO_ROUTE: dict[str, str] = {v: k for k, v in AGENT_UUIDS.items()}

# Agents tag the coordinator back in their reply, so verdicts arrive with a
# leading @[[uuid]] token. Strip it so the C++ coordinator gets clean JSON.
_MENTION_RE = re.compile(r"^\s*(@\[\[[0-9a-fA-F-]+\]\]\s*)+")


def strip_mentions(text: str) -> str:
    return _MENTION_RE.sub("", text).strip()


_FENCE_OPEN = re.compile(r"^```[a-zA-Z]*\s*")
_FENCE_CLOSE = re.compile(r"\s*```$")


def clean_reply(text: str) -> str:
    """Return a verdict as clean JSON.

    Agents are inconsistent: some reply with bare JSON, some wrap it in markdown
    code fences, some tag the coordinator first. Strip the mention, strip any
    fence, then extract the JSON object so every consumer gets parseable JSON.
    """
    t = strip_mentions(text)
    t = _FENCE_OPEN.sub("", t.strip())
    t = _FENCE_CLOSE.sub("", t.strip())
    start, end = t.find("{"), t.rfind("}")
    if start != -1 and end > start:
        t = t[start:end + 1]
    return t.strip()

FIRE_AND_FORGET: set[str] = {"01-logger", "14-harness-logger"}

# One queue of waiting futures per route. A queue, not a single slot, so two
# concurrent calls to the same agent do not overwrite each other — replies match
# the oldest waiting caller first.
pending: dict[str, "deque[asyncio.Future[str]]"] = {}

link: BandLink | None = None


async def _send_to_session(payload: str, agent_uuid: str) -> None:
    await link.rest.agent_api_messages.create_agent_chat_message(
        chat_id=SESSION_ROOM_ID,
        message=ChatMessageRequest(
            content=payload,
            mentions=[ChatMessageRequestMentionsItem(id=agent_uuid)],
        ),
        request_options=DEFAULT_REQUEST_OPTIONS,
    )


async def handle_agent_request(request: web.Request) -> web.Response:
    route = request.match_info["name"]
    body = await request.text()
    agent_uuid = AGENT_UUIDS.get(route)

    if not agent_uuid:
        logger.error("Unknown route: %s", route)
        return web.Response(status=404)

    mention = MENTION_TEMPLATE.format(uuid=agent_uuid)
    payload = mention + body

    try:
        await _send_to_session(payload, agent_uuid)
    except Exception as exc:
        logger.error("Send failed for %s: %s", route, exc)
        return web.Response(
            content_type="application/json",
            text=json.dumps({
                "agent": route, "status": "error",
                "error_code": "SEND_FAILED",
            }),
        )

    if route in FIRE_AND_FORGET:
        return web.Response(
            content_type="application/json",
            text=json.dumps({"agent": route, "status": "logged"}),
        )

    loop = asyncio.get_event_loop()
    fut: asyncio.Future[str] = loop.create_future()
    pending.setdefault(route, deque()).append(fut)

    try:
        result = await asyncio.wait_for(fut, timeout=REPLY_TIMEOUT)
        return web.Response(content_type="application/json", text=result)
    except asyncio.TimeoutError:
        logger.warning("Timeout waiting for %s", route)
        return web.Response(
            content_type="application/json",
            text=json.dumps({
                "agent": route, "status": "error",
                "error_code": "BRIDGE_TIMEOUT",
            }),
        )
    finally:
        dq = pending.get(route)
        if dq and fut in dq:
            dq.remove(fut)


async def event_listener() -> None:
    async for event in link:
        if isinstance(event, RoomAddedEvent):
            if event.room_id == SESSION_ROOM_ID:
                await link.subscribe_room(event.room_id)
            continue

        if not isinstance(event, MessageEvent):
            continue

        sender_id = event.payload.sender_id
        if sender_id == COORDINATOR_AGENT_ID:
            continue

        route = UUID_TO_ROUTE.get(sender_id or "")
        if not route:
            continue

        dq = pending.get(route)
        if dq:
            for fut in list(dq):
                if not fut.done():
                    content = clean_reply(event.payload.content or "{}")
                    logger.info("Verdict received from %s", route)
                    fut.set_result(content)
                    break


async def main() -> None:
    global link

    if not COORDINATOR_AGENT_ID or not COORDINATOR_API_KEY:
        raise RuntimeError(
            "COORDINATOR_AGENT_ID and COORDINATOR_API_KEY must be set in .env"
        )
    if not SESSION_ROOM_ID:
        raise RuntimeError(
            "SESSION_ROOM_ID must be set in .env — run setup_session.py first"
        )

    link = BandLink(agent_id=COORDINATOR_AGENT_ID, api_key=COORDINATOR_API_KEY)
    await link.connect()
    await link.subscribe_agent_rooms(COORDINATOR_AGENT_ID)
    await link.subscribe_room(SESSION_ROOM_ID)
    logger.info("Subscribed to session room %s", SESSION_ROOM_ID)

    asyncio.create_task(event_listener())

    app = web.Application()
    app.router.add_post("/api/agent/{name}", handle_agent_request)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", BRIDGE_PORT).start()

    logger.info("Band bridge listening on port %d", BRIDGE_PORT)
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
