#!/usr/bin/env python3
"""
Band Bridge

Translates the C++ coordinator's sync HTTP calls into Band async messages.
Runs on port 5000, matching the mock_server interface exactly.
The C++ coordinator needs BAND_HOST=http://127.0.0.1:5000 (unchanged).

Setup required before first run:
  1. Register the coordinator as a Band agent — get its agent_id and api_key.
  2. Create a DM room between the coordinator and each specialist agent.
  3. Set all env vars in coordinator/.env (see ROOM_* vars below).
  4. Run: python3 band_bridge.py
"""

import asyncio
import json
import logging
import os

from aiohttp import web
from band.client.rest import ChatMessageRequest, DEFAULT_REQUEST_OPTIONS
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

FIRE_AND_FORGET: set[str] = {"01-logger", "14-harness-logger"}

agent_to_room: dict[str, str] = {}
room_to_agent: dict[str, str] = {}

pending: dict[str, "asyncio.Future[str]"] = {}

link: BandLink | None = None


def _load_rooms_from_env() -> None:
    for route, agent_uuid in AGENT_UUIDS.items():
        env_key = "ROOM_" + route.upper().replace("-", "_")
        room_id = os.getenv(env_key, "").strip()
        if room_id:
            agent_to_room[agent_uuid] = room_id
            room_to_agent[room_id] = agent_uuid
            logger.info("Room configured: %s -> %s", route, room_id)
        else:
            logger.warning("No room env var set for %s (expected %s)", route, env_key)


async def _subscribe_all_rooms() -> None:
    for room_id in room_to_agent:
        await link.subscribe_room(room_id)
        logger.info("Subscribed to room %s", room_id)


async def _send_to_room(room_id: str, payload: str) -> None:
    await link.rest.agent_api_messages.create_agent_chat_message(
        chat_id=room_id,
        message=ChatMessageRequest(content=payload),
        request_options=DEFAULT_REQUEST_OPTIONS,
    )


async def handle_agent_request(request: web.Request) -> web.Response:
    route = request.match_info["name"]
    body = await request.text()
    agent_uuid = AGENT_UUIDS.get(route)

    if not agent_uuid:
        logger.error("Unknown route: %s", route)
        return web.Response(status=404)

    room_id = agent_to_room.get(agent_uuid)
    if not room_id:
        logger.error("No room for route %s", route)
        return web.Response(
            content_type="application/json",
            text=json.dumps({
                "agent": route, "status": "violation",
                "certainty": "violation", "error_code": "NO_ROOM_CONFIGURED",
            }),
        )

    try:
        await _send_to_room(room_id, body)
    except Exception as exc:
        logger.error("Send failed for %s: %s", route, exc)
        return web.Response(
            content_type="application/json",
            text=json.dumps({
                "agent": route, "status": "violation",
                "certainty": "violation", "error_code": "SEND_FAILED",
            }),
        )

    if route in FIRE_AND_FORGET:
        return web.Response(
            content_type="application/json",
            text=json.dumps({"agent": route, "status": "logged"}),
        )

    loop = asyncio.get_event_loop()
    fut: asyncio.Future[str] = loop.create_future()
    pending[route] = fut

    try:
        result = await asyncio.wait_for(fut, timeout=2.3)
        return web.Response(content_type="application/json", text=result)
    except asyncio.TimeoutError:
        logger.warning("Timeout waiting for %s", route)
        return web.Response(
            content_type="application/json",
            text=json.dumps({
                "agent": route, "status": "violation",
                "certainty": "violation", "error_code": "BRIDGE_TIMEOUT",
            }),
        )
    finally:
        pending.pop(route, None)


async def event_listener() -> None:
    async for event in link:
        if isinstance(event, RoomAddedEvent):
            if event.room_id not in room_to_agent:
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

        fut = pending.get(route)
        if fut and not fut.done():
            content = event.payload.content or "{}"
            logger.info("Verdict received from %s", route)
            fut.set_result(content)


async def main() -> None:
    global link

    if not COORDINATOR_AGENT_ID or not COORDINATOR_API_KEY:
        raise RuntimeError(
            "COORDINATOR_AGENT_ID and COORDINATOR_API_KEY must be set in .env"
        )

    _load_rooms_from_env()

    link = BandLink(agent_id=COORDINATOR_AGENT_ID, api_key=COORDINATOR_API_KEY)
    await link.connect()
    await link.subscribe_agent_rooms(COORDINATOR_AGENT_ID)
    await _subscribe_all_rooms()

    asyncio.create_task(event_listener())

    app = web.Application()
    app.router.add_post("/api/agent/{name}", handle_agent_request)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", 5000).start()

    logger.info("Band bridge listening on port 5000")
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
