"""api.routes.live — Server-Sent Events for live dashboard refresh."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone

from flask import Blueprint, Response, request, stream_with_context

from api.controllers import live_controller

live_bp = Blueprint("live", __name__, url_prefix="/api")

STREAM_POLL_INTERVAL_S = 2.0
STREAM_KEEPALIVE_INTERVAL_S = 15.0


@live_bp.route("/live/stream", methods=["GET"])
def live_stream() -> Response:
    """GET /api/live/stream — emit SSE updates when DB-backed live state changes."""
    charger_id = request.args.get("charger_id") or None
    session_id = request.args.get("session_id") or None

    @stream_with_context
    def generate():
        last_signature = ""
        last_ping_at = time.monotonic()

        while True:
            snapshot = live_controller.build_snapshot(
                charger_id=charger_id,
                session_id=session_id,
            )
            signature = snapshot.get("signature", "")

            if signature != last_signature:
                yield _format_sse("update", snapshot)
                last_signature = signature
                last_ping_at = time.monotonic()
            elif time.monotonic() - last_ping_at >= STREAM_KEEPALIVE_INTERVAL_S:
                yield _format_sse(
                    "ping",
                    {
                        "scope": {
                            "charger_id": charger_id,
                            "session_id": session_id,
                        },
                        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
                    },
                )
                last_ping_at = time.monotonic()

            time.sleep(STREAM_POLL_INTERVAL_S)

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def _format_sse(event: str, payload: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(payload, separators=(',', ':'))}\n\n"
