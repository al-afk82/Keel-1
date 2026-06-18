#!/usr/bin/env python3
"""
Session setup.

Creates one shared Band session and adds the coordinator plus every specialist
agent as participants. Run this once. It prints the SESSION_ROOM_ID line you
paste into coordinator/.env, then the bridge operates inside that single room.

Auth: uses the human user key (band_u_...) via X-API-Key.
Set BAND_USER_KEY in coordinator/.env before running.

Usage:
  python3 setup_session.py
"""

import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://app.band.ai/api/v1"
USER_KEY = os.getenv("BAND_USER_KEY", "").strip()
COORDINATOR_AGENT_ID = os.getenv("COORDINATOR_AGENT_ID", "").strip()

# Coordinator plus the thirteen specialists. Keep in sync with band_bridge.py.
AGENT_UUIDS = {
    "01-logger":               "b4fa1211-d6a7-4171-9351-d633d83bd06c",
    "03-human-profiler":       "5d486be4-f3fd-4e79-9da5-18cf10ca2f45",
    "04-engine-profiler":      "2a4b901a-c078-4a7f-bc80-bfe0e779c7d8",
    "05-alignment-classifier": "007d56f5-6695-47ce-be88-c245586adf59",
    "06-question-generator":   "71a21a6f-3af3-4408-99f1-f811ed562462",
    "07-gap-analyzer":         "db01f764-6518-4aed-be28-14a97ec043eb",
    "08-constraints-checker":  "311e1eb1-a3de-4541-b3bb-a2db48b1239f",
    "09-anti-patterns-checker":"0d062438-b3fe-47c8-bb36-9334465b2868",
    "10-voice-checker":        "2576cb68-7675-4903-ae62-ee7e22267a4f",
    "11-quality-checker":      "d338c531-e1df-4952-ab33-a71a8407a798",
    "12-identity-agent":       "ed23a4ac-ac52-444c-bd23-fb33c1a23346",
    "13-verifier":             "00545343-7a7b-493a-828d-71ec34b1bfd1",
    "14-harness-logger":       "d3e3a448-31db-45b0-8b6e-b1a65984bc58",
}

SESSION_TITLE = "Drift Detection"


def create_session() -> str:
    resp = requests.post(
        f"{BASE_URL}/me/chats",
        headers={"X-API-Key": USER_KEY},
        json={"chat": {"title": SESSION_TITLE}},
        timeout=15,
    )
    resp.raise_for_status()
    room_id = resp.json()["data"]["id"]
    print(f"Created session: {room_id}")
    return room_id


def add_participant(room_id: str, participant_id: str, label: str) -> None:
    resp = requests.post(
        f"{BASE_URL}/me/chats/{room_id}/participants",
        headers={"X-API-Key": USER_KEY},
        json={"participant": {"participant_id": participant_id, "role": "member"}},
        timeout=15,
    )
    if resp.status_code in (200, 201):
        print(f"  added {label}")
    else:
        print(f"  FAILED {label}: {resp.status_code} {resp.text}")


def main() -> None:
    if not USER_KEY:
        sys.exit("BAND_USER_KEY is not set in .env")
    if not COORDINATOR_AGENT_ID:
        sys.exit("COORDINATOR_AGENT_ID is not set in .env")

    room_id = create_session()

    add_participant(room_id, COORDINATOR_AGENT_ID, "coordinator")
    for route, agent_uuid in AGENT_UUIDS.items():
        add_participant(room_id, agent_uuid, route)

    print()
    print("Paste this into coordinator/.env:")
    print(f"SESSION_ROOM_ID={room_id}")


if __name__ == "__main__":
    main()
